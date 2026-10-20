"""
Conversational memory: deterministic handling of what a person tells MEMORA
and what they ask it to recall.

Principles
----------
- Every stored fact records its provenance (who said it, when) and is
  restated with that attribution ("You told me today that ...").
- Questions are answered only from records that match the topic asked about.
  When nothing matches, MEMORA says so instead of offering an unrelated memory.
- Conflicting statements supersede older ones without deleting them, and the
  person is told what changed.
- Object answers come only from real observations, phrased as "last seen"
  with their age; MEMORA never states a current location as fact.
- Names are only learned from explicit introductions ("my name is ...").
- Urgent statements are left to the safety layer (this module returns None).

Facts are stored in the existing relevant_memories table. Structured fields
live in tags (``fact_key:``, ``fact_value:``, ``polarity:``, ``status:``,
``source:``) so no schema migration is required.
"""

from __future__ import annotations

import dataclasses
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from src.clinical.urgent_safety import detect_urgent_concern
from src.cognition.memory_models import MemoryImportance, MemoryType, RelevantMemory

FACT_TAG = "user_fact"
PREFERENCE_TAG = "user_preference"
PREFERRED_NAME_KEY = "user_preferred_name"
EMERGENCY_NUMBER_KEY = "emergency_number"
TRUSTED_CONTACT_KEY = "trusted_contact"

RELATIONS = ("daughter", "son", "wife", "husband", "partner", "doctor", "caregiver", "nurse", "brother",
             "sister", "mother", "father", "grandson", "granddaughter", "friend", "neighbor", "neighbour")

# Relations a person normally has only one of; a new value replaces the old one.
SINGLE_VALUED_RELATIONS = {"wife", "husband", "partner", "mother", "father"}
PRONOUNS = {"it", "that", "this", "them", "those", "these", "they", "him", "her", "one"}
NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

CATEGORIES = {
    "drink": {"tea", "coffee", "juice", "water", "milk", "lemonade", "soda", "cocoa", "chai", "wine", "beer"},
    "sport": {"cricket", "football", "soccer", "tennis", "golf", "badminton", "hockey", "basketball",
              "baseball", "swimming", "chess", "rugby", "volleyball"},
    "food": {"rice", "bread", "pasta", "soup", "curry", "fish", "chicken", "salad", "cake", "biscuits",
             "cookies", "fruit", "apples", "bananas", "chocolate", "pizza", "eggs", "cheese"},
    "music": {"music", "jazz", "songs", "singing", "classical", "piano", "guitar", "radio"},
}
CATEGORY_WORDS = {"drink": {"drink", "drinks", "beverage"}, "sport": {"sport", "sports", "game", "games"},
                  "food": {"food", "eat", "meal", "dish"}, "music": {"music", "song", "songs"}}

KNOWN_OBJECTS = ("reading glasses", "glasses", "spectacles", "keys", "wallet", "purse", "remote", "phone",
                 "cell phone", "mobile", "bottle", "water bottle", "medication", "medicine", "pills",
                 "cane", "walking cane", "hearing aid", "watch", "book", "bag", "handbag", "shoes",
                 "slippers", "cup", "mug", "laptop", "charger", "umbrella", "coat", "jacket", "hat")

NAME_STOPWORDS = {
    "tired", "fine", "good", "ok", "okay", "here", "there", "ready", "sorry", "sure", "not", "so", "very",
    "happy", "sad", "hungry", "thirsty", "cold", "hot", "warm", "busy", "lost", "confused", "scared",
    "worried", "afraid", "home", "back", "done", "well", "unwell", "sick", "better", "great", "alright",
    "today", "now", "going", "looking", "trying", "feeling", "just", "still", "bored", "lonely", "awake",
    "sleepy", "late", "early", "alone", "old", "new", "glad", "angry", "upset", "fed", "afraid",
}

_FIRST_TO_SECOND = [(r"\bi am\b", "you are"), (r"\bi'm\b", "you're"), (r"\bi was\b", "you were"),
                    (r"\bi\b", "you"), (r"\bmy\b", "your"), (r"\bme\b", "you"), (r"\bmine\b", "yours"),
                    (r"\bmyself\b", "yourself")]


def _to_second_person(text: str) -> str:
    out = text.strip().rstrip(".!")
    out = re.sub(r"\s+(now|these days|nowadays|anymore|any more)$", "", out, flags=re.IGNORECASE)
    for pat, rep in _FIRST_TO_SECOND:
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    return out


def _when(ts: Optional[datetime], now: datetime) -> str:
    if ts is None:
        return "earlier"
    if ts.date() == now.date():
        return "today"
    if ts.date() == (now - timedelta(days=1)).date():
        return "yesterday"
    return f"on {ts.strftime('%B')} {ts.day}"


def _age_phrase(ts: datetime, now: datetime) -> str:
    secs = max(0.0, (now - ts).total_seconds())
    if secs < 90:
        return "just now"
    if secs < 3600:
        return f"about {int(round(secs / 60))} minutes ago"
    if ts.date() == now.date():
        hours = int(secs // 3600)
        return f"about {hours} hour{'s' if hours != 1 else ''} ago"
    if ts.date() == (now - timedelta(days=1)).date():
        return f"yesterday at {ts.strftime('%I:%M %p').lstrip('0')}"
    return f"on {ts.strftime('%B')} {ts.day}"


def _norm(text: str) -> str:
    t = text.lower().replace("’", "'").strip()
    t = re.sub(r"\bfavourite\b", "favorite", t)
    t = re.sub(r"\bcolour\b", "color", t)
    t = re.sub(r"\bflavour\b", "flavor", t)
    return re.sub(r"\s+", " ", t)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _category_of(text: str) -> Optional[str]:
    w = _words(text)
    for cat, vocab in CATEGORIES.items():
        if w & vocab:
            return cat
    return None


@dataclass
class StoredFact:
    memory_id: str
    key: str
    value: str
    polarity: str  # "positive" | "negative"
    statement: str
    timestamp: Optional[datetime]
    status: str
    source: str
    category: Optional[str]


class ConversationalMemory:
    """Answers recall questions and records user-provided facts."""

    def __init__(self, database: Any, clock: Callable[[], datetime] = datetime.now,
                 visual_memory: Any = None, appointments: Any = None, medications: Any = None) -> None:
        self.db = database
        self.clock = clock
        # Optional VisualEpisodicMemoryEngine holding richer in-session sightings.
        self.visual_memory = visual_memory
        # Optional AppointmentManager; appointments must be entered by the person or a carer.
        self.appointments = appointments
        # Optional MedicationManager; doses are only ever *reported* taken.
        self.medications = medications
        self.search_history: list[dict] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def respond(self, speech: Optional[str], face_id: Optional[str] = None,
                patient_name: Optional[str] = None) -> Optional[str]:
        """Return a direct answer for speech, or None if another layer should reply."""
        if not speech or not speech.strip():
            return None
        if detect_urgent_concern(speech) is not None:
            return None  # the safety layer owns this turn
        t = _norm(speech)
        for handler in (self._capability_boundaries, self._name_correction_or_question, self._name_introduction,
                        self._orientation, self._forget, self._relation_correction, self._relations_have,
                        self._fact_correction_or_statement,
                        self._fact_question, self._timeline, self._visitors, self._last_search,
                        self._medication_report, self._medication_question, self._appointment,
                        self._object_location, self._feelings, self._small_talk):
            reply = handler(speech, t, face_id=face_id, patient_name=patient_name)
            if reply:
                return reply
        return None

    _FEELINGS = {
        "tired": "I'm sorry you're feeling tired. It might help to sit and rest for a little while.",
        "sleepy": "It sounds like you could use some rest. Take it easy.",
        "sad": "I'm sorry you're feeling sad. I'm here with you. Would you like to talk about it?",
        "lonely": "I'm sorry you're feeling lonely. Maybe it's a good moment to call someone you like talking to.",
        "bored": "Maybe we could find something you enjoy doing. You can tell me what you like.",
        "hungry": "It might be a good time for something to eat.",
        "thirsty": "A glass of water might help.",
        "cold": "Maybe a warm layer or a blanket would help.",
        "happy": "I'm glad to hear that.",
        "good": "I'm glad to hear that.",
        "fine": "I'm glad to hear that.",
    }

    def _feelings(self, raw: str, t: str, **_) -> Optional[str]:
        m = re.match(r"^(?:i'm feeling|i am feeling|i feel|i am|i'm) (?:a bit |a little |very |so |really |quite )?([a-z]+)\b", t)
        if m and m.group(1) in self._FEELINGS:
            return self._FEELINGS[m.group(1)]
        return None

    def _small_talk(self, raw: str, t: str, patient_name=None, **_) -> Optional[str]:
        if re.match(r"^(hi|hello|hey|good (morning|afternoon|evening))\b[\w ,!.]{0,20}$", t):
            return self.greeting(patient_name)
        if re.match(r"^(thanks|thank you)\b", t):
            return "You're welcome."
        return None

    _MEDS = r"(pills?|tablets?|medicines?|medications?|meds|doses?|prescriptions?|insulin|inhaler)"

    def _capability_boundaries(self, raw: str, t: str, **_) -> Optional[str]:
        """
        Requests MEMORA cannot fulfil, answered plainly so nobody believes an action
        happened: contacting people, and medical or medication advice.
        """
        contact = self.get_setting(TRUSTED_CONTACT_KEY)
        offer = f" Your trusted contact is {contact}, if you'd like to call them." if contact else ""
        if re.search(r"\b(did|have|has|could|can) (you|memora) (already )?(call|called|phone|phoned|ring|rang|contact|contacted|"
                     r"tell|told|message|messaged|text|texted|email|emailed|notify|notified|alert|alerted|send|sent)\b", t) \
                or re.match(r"^(please |can you |could you |would you |will you )?(call|phone|ring|text|message|email|contact|"
                            r"notify|alert)\b(?! me\b)", t) \
                or re.match(r"^(please |can you |could you |would you )?(tell|let) (?!me\b)\w+", t) and re.search(r"\b(know|tell)\b", t) \
                or re.search(r"\bsend (a |an )?(message|text|email|alert)\b", t):
            return "I can't make calls or send messages, so I haven't contacted anyone." + offer
        if re.search(rf"\b(should|can|could|may|do|must) i (take|stop|skip|double|have|increase|reduce|cut|change|miss)\b.*\b{self._MEDS}\b", t) \
                or re.search(rf"\b(extra|another|more|second) {self._MEDS}\b", t) \
                or re.search(rf"\bis it (safe|ok|okay|alright) to (take|stop|skip|mix|double)\b", t):
            return ("I can't give advice about medicines. Please ask your doctor or pharmacist before "
                    "taking, skipping or changing anything. If you think you've taken too much, "
                    "call your emergency number now.")
        if re.search(r"\b(am i (sick|ill|unwell|dying|ok|okay|alright)|do i have (dementia|alzheimer'?s|a cold|covid|"
                     r"cancer|diabetes|an infection)|is something wrong with me|what is wrong with me|what's wrong with me|"
                     r"what illness do i have)\b", t):
            return ("I'm sorry you're worried. I can't tell whether you're unwell or give a diagnosis. "
                    "If you feel unwell, please contact your doctor, or call your emergency number if it feels serious.")
        return None

    def fallback_reply(self, patient_name: Optional[str] = None) -> str:
        return ("I'm not sure I understood. You can tell me something to remember, "
                "ask me what you've told me, or ask where I last saw something.")

    def greeting(self, patient_name: Optional[str] = None) -> str:
        hour = self.clock().hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        return f"Good {part}{', ' + patient_name if patient_name else ''}. How can I help?"

    # ------------------------------------------------------------------
    # Preferred name (user-provided, persisted)
    # ------------------------------------------------------------------

    def get_preferred_name(self) -> Optional[str]:
        getter = getattr(self.db, "_get_system_state", None)
        return getter(PREFERRED_NAME_KEY) if getter else None

    def get_setting(self, key: str) -> Optional[str]:
        getter = getattr(self.db, "_get_system_state", None)
        return getter(key) if getter else None

    def _name_introduction(self, raw: str, t: str, face_id=None, **_) -> Optional[str]:
        m = re.match(r"^(?:hi|hello|hey)?[, ]*(?:my name is|my name's|call me|you can call me)\s+([a-z][a-z'\-]{1,30})[.!]?$", t)
        explicit = bool(m)
        if not m:
            m = re.match(r"^(?:hi|hello|hey)?[, ]*(?:i am|i'm|this is|it's|it is)\s+([a-z][a-z'\-]{1,30})[.!]?$", t)
        if not m:
            return None
        candidate = m.group(1)
        if candidate in NAME_STOPWORDS:
            return None
        if not explicit:
            # "I'm Sid" is accepted only when the name was written/transcribed with a
            # capital letter, so "i'm tired" style statements are never taken as names.
            original = re.search(rf"\b({re.escape(candidate)})\b", raw, flags=re.IGNORECASE)
            if not original or not original.group(1)[0].isupper():
                return None
        name = candidate[0].upper() + candidate[1:]

        if face_id and hasattr(self.db, "get_identity") and self.db.get_identity(face_id):
            # The speaker is a recognised face: label that identity, relationship unknown.
            self.db.bind_name(face_id, name, relationship=None)
            return f"Nice to meet you, {name}. I'll remember your name."

        setter = getattr(self.db, "_set_system_state", None)
        if setter:
            setter(PREFERRED_NAME_KEY, name)
        return f"Nice to meet you, {name}. I'll call you {name}."

    # ------------------------------------------------------------------
    # Orientation (system clock is the only verified source)
    # ------------------------------------------------------------------

    def _orientation(self, raw: str, t: str, **_) -> Optional[str]:
        now = self.clock()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        date_str = f"{now.strftime('%A')}, {now.strftime('%B')} {now.day}, {now.year}"
        if re.search(r"\bwhat(?:'s| is)? the time\b|\bwhat time is it\b|\bwhat time it is\b", t):
            return f"It's {time_str}."
        if re.search(r"\bwhat(?:'s| is)? (?:the )?(?:day|date)(?: today)?\b|\bwhat day is it\b|\bwhat is today\b|\bwhat's today\b|\bwhich day\b", t):
            return f"Today is {date_str}."
        if re.search(r"\bwhat (?:month|year) is it\b", t):
            return f"It's {now.strftime('%B')} {now.year}."
        if re.search(r"\b(who|what) are you\b", t):
            return ("I'm MEMORA, a memory assistant. I can remember things you tell me, "
                    "and tell you where I last saw your things.")
        if re.search(r"\bwhere am i\b", t):
            return ("I can't tell exactly where you are from here. Take your time and look around "
                    "for something familiar. If you feel unsure, call someone you trust.")
        return None

    # ------------------------------------------------------------------
    # Facts
    # ------------------------------------------------------------------

    def _parse_statement(self, t: str) -> Optional[tuple[str, str, str, bool]]:
        """Return (key, value, polarity, single_valued) for a fact statement."""
        if "?" in t or re.match(r"^(what|who|where|when|how|do|does|did|is|are|can|could|which)\b", t):
            return None
        t = t.rstrip(".! ")
        rel = "|".join(RELATIONS)
        m = re.match(rf"^(?:and )?my ({rel})(?:'s name)? is (?:called |named )?(?!not\b)([a-z][a-z .'\-]{{0,40}})$", t)
        if m:
            relation = m.group(1)
            return f"relation:{relation}", m.group(2).strip(), "positive", relation in SINGLE_VALUED_RELATIONS
        m = re.match(r"^(?:and )?my favorite ([a-z ]{2,30}?) is ([a-z0-9][a-z0-9 '\-]{0,40})$", t)
        if m:
            return f"favorite:{m.group(1).strip()}", m.group(2).strip(), "positive", True
        m = re.match(r"^i (?:really |also )?(?:do not|don't|dont) (?:like|enjoy|want) ([a-z0-9][a-z0-9 '\-]{0,50})$", t) \
            or re.match(r"^i (?:hate|dislike|can't stand|cannot stand) ([a-z0-9][a-z0-9 '\-]{0,50})$", t)
        if m:
            value = re.sub(r"\b(anymore|any more|now)\b", "", m.group(1)).strip()
            return f"likes:{value}", value, "negative", False
        m = re.match(r"^i (?:really |also |usually )?prefer ([a-z0-9][a-z0-9 '\-]{0,50})$", t)
        if m:
            value = re.sub(r"\b(now|these days|nowadays)\b", "", m.group(1)).strip()
            cat = _category_of(value) or value
            return f"prefers:{cat}", value, "positive", True
        m = re.match(r"^i (?:really |also |usually )?(?:like|love|enjoy) ([a-z0-9][a-z0-9 '\-]{0,50})$", t)
        if m:
            value = m.group(1).strip()
            return f"likes:{value}", value, "positive", False
        return None

    def _fact_correction_or_statement(self, raw: str, t: str, face_id=None, **_) -> Optional[str]:
        parsed = self._parse_statement(t)
        if not parsed:
            return None
        key, value, polarity, single_valued = parsed
        if value.strip().lower() in PRONOUNS:
            return (f"What do you mean by '{value.strip()}'? Tell me what it is, for example "
                    "'I like jasmine tea', and I'll remember it.")
        statement = raw.strip().rstrip(".!")
        others = [f for f in self.active_facts() if key.startswith("relation:") and not single_valued
                  and f.key == key and f.value.lower() != value.lower()]
        superseded = []
        for f in self.active_facts():
            same_key_conflict = single_valued and f.key == key and f.value != value
            polarity_flip = (f.value == value and f.polarity != polarity
                             and f.key.split(":")[0] in ("likes", "prefers") and key.split(":")[0] in ("likes", "prefers"))
            if same_key_conflict or polarity_flip:
                superseded.append(f)
            elif f.key == key and f.value == value and f.polarity == polarity:
                return f"I already have that noted: {_to_second_person(f.statement)}."

        new_id = f"fact_{uuid.uuid4().hex}"
        self._save_fact(new_id, key, value, polarity, statement)
        for f in superseded:
            self._mark_superseded(f, new_id)
        if superseded:
            old = "; ".join(_to_second_person(f.statement) for f in superseded)
            return f"Thank you, I've updated that. Earlier you told me: {old}. Now I have: {_to_second_person(statement)}."
        if others:
            relation = key.split(":", 1)[1]
            names = [o.value.title() for o in others] + [value.title()]
            return (f"I'll remember that {_to_second_person(statement)}. You've also told me about "
                    f"{' and '.join(n for n in names[:-1])}, so I now have more than one {relation}: "
                    f"{', '.join(names)}. If one of these is wrong, say for example "
                    f"'my {relation} is not {names[0]}'.")
        return f"I'll remember that {_to_second_person(statement)}."

    def _retract(self, fact: "StoredFact", reason: str) -> None:
        mem = next((m for m in self._raw_fact_memories() if m.memory_id == fact.memory_id), None)
        if mem is None:
            return
        tags = [tg for tg in mem.tags if not tg.startswith("status:")] + ["status:retracted", f"retracted_reason:{reason}"]
        self._repo().save(dataclasses.replace(mem, tags=tags))

    def _relation_correction(self, raw: str, t: str, **_) -> Optional[str]:
        """'My daughter is not Riya' / 'No, my daughter's name is Priya, not Riya'."""
        rel = "|".join(RELATIONS)
        t = t.rstrip(".! ")
        m = re.match(rf"^(?:no,? )?my ({rel})(?:'s name)? (?:is not|isn't|is n't) (?:called |named )?([a-z][a-z .'\-]{{0,40}})$", t)
        replace_with = None
        if not m:
            m2 = re.match(rf"^(?:no,? )?my ({rel})(?:'s name)? is (?:called |named )?([a-z][a-z .'\-]{{0,40}}?),? not ([a-z][a-z .'\-]{{0,40}})$", t)
            if not m2:
                return None
            relation, replace_with, wrong = m2.group(1), m2.group(2).strip(), m2.group(3).strip()
        else:
            relation, wrong = m.group(1), m.group(2).strip()
        matches = [f for f in self.active_facts() if f.key == f"relation:{relation}" and f.value.lower() == wrong.lower()]
        for f in matches:
            self._retract(f, "corrected by person")
        reply = (f"Thank you for correcting me. I won't say your {relation} is {wrong.title()} any more."
                 if matches else f"I didn't have your {relation} noted as {wrong.title()}.")
        if replace_with:
            statement = f"My {relation} is {replace_with.title()}"
            if not any(f.key == f"relation:{relation}" and f.value.lower() == replace_with.lower() for f in self.active_facts()):
                self._save_fact(f"fact_{uuid.uuid4().hex}", f"relation:{relation}", replace_with.lower(), "positive", statement)
            reply += f" I've noted that your {relation} is {replace_with.title()}."
        return reply

    def _relations_have(self, raw: str, t: str, **_) -> Optional[str]:
        """'I have two daughters, Riya and Priya' / 'I have a son called Leo'."""
        rel = "|".join(RELATIONS)
        m = re.match(rf"^i have (a|an|one|two|three|four|five) ({rel})s?,? (?:named |called |who (?:is|are) called )?"
                     rf"([a-z][a-z .'\-]{{0,60}})[.!]?$", t)
        if not m:
            return None
        relation = m.group(2)
        names = [n.strip() for n in re.split(r",| and ", m.group(3)) if n.strip()]
        if not names or len(names) > 5 or any(n in PRONOUNS for n in names):
            return None
        stored = []
        for name in names:
            if not any(f.key == f"relation:{relation}" and f.value.lower() == name.lower() for f in self.active_facts()):
                self._save_fact(f"fact_{uuid.uuid4().hex}", f"relation:{relation}", name.lower(), "positive",
                                f"My {relation} is {name.title()}")
                stored.append(name.title())
        if not stored:
            return f"I already have that noted."
        return f"I'll remember that your {relation}{'s are' if len(stored) > 1 else ' is'} {' and '.join(stored)}."

    def _forget(self, raw: str, t: str, **_) -> Optional[str]:
        m = re.match(r"^(?:please )?forget (?:that |about )?(.+?)[.!]?$", t)
        if not m:
            return None
        what = m.group(1).strip()
        if what in ("everything", "it all", "all of it", "all that", "everything about me"):
            return ("To delete everything I've stored, use /delete-all - it asks you to confirm first. "
                    "To remove one thing, use /memories and then /forget with its number.")
        parsed = self._parse_statement(what)
        targets = []
        if parsed:
            key, value = parsed[0], parsed[1]
            targets = [f for f in self.active_facts() if f.key == key and f.value.lower() == value.lower()]
        if not targets:
            words = _words(what) - {"i", "my", "me", "the", "a", "is", "that", "like", "love"}
            targets = [f for f in self.active_facts() if words and words <= _words(f.statement)]
        if not targets:
            return "I couldn't find that in what you've told me, so nothing was changed."
        for f in targets:
            self._retract(f, "person asked to forget")
        return "Okay, I won't use that any more: " + "; ".join(_to_second_person(f.statement) for f in targets) + "."

    def _name_correction_or_question(self, raw: str, t: str, **_) -> Optional[str]:
        name = self.get_preferred_name()
        if re.match(r"^(?:no,? )?(?:my name is not|my name isn't|that's not my name|that is not my name|"
                    r"don't call me|do not call me)\b", t):
            setter = getattr(self.db, "_set_system_state", None)
            if setter and name:
                setter(PREFERRED_NAME_KEY, "")
            return "I'm sorry about that. What would you like me to call you? You can say: my name is ..."
        if re.search(r"\b(what(?:'s| is) my name|who am i|do you know (?:my name|who i am))\b", t):
            if name:
                return f"You told me your name is {name}."
            return "You haven't told me your name yet. You can say: my name is ..."
        return None

    def _fact_question(self, raw: str, t: str, **_) -> Optional[str]:
        now = self.clock()
        rel = "|".join(RELATIONS)
        facts = self.active_facts()

        m = re.search(rf"\b(?:who is|who's) my ({rel})\b|\bwhat(?:'s| is) my ({rel})(?:'s)? (?:name|called)\b|"
                      rf"\bwhat my ({rel}) is called\b|\bwhat(?:'s| is) the name of my ({rel})\b", t)
        if m:
            relation = next(g for g in m.groups() if g)
            hits = [f for f in facts if f.key == f"relation:{relation}"]
            if len(hits) > 1:
                return (f"You've told me about more than one {relation}. "
                        + self._answer(hits, now, limit=5))
            return self._answer(hits, now) or f"I don't know who your {relation} is yet. You can tell me, and I'll remember."

        m = re.search(r"\bwhat(?:'s| is) my favorite ([a-z ]{2,30}?)\??$", t)
        if m:
            topic = m.group(1).strip()
            hits = [f for f in facts if f.key == f"favorite:{topic}"]
            return self._answer(hits, now) or f"You haven't told me your favorite {topic} yet."

        m = re.match(r"^do i (?:like|enjoy|love|prefer) ([a-z0-9][a-z0-9 '\-]{0,40}?)\??$", t)
        if m:
            topic_words = _words(m.group(1))
            hits = [f for f in facts if f.key.split(":")[0] in ("likes", "prefers") and topic_words & _words(f.value)]
            return self._answer(hits, now) or f"You haven't told me whether you like {m.group(1)}."

        if re.search(r"\bwhat (?:are|were) my (?:hobbies|interests)\b|\bwhat do i (?:like|enjoy|love) doing\b", t):
            likes = [f for f in facts if f.key.split(":")[0] in ("likes", "prefers", "favorite") and f.polarity == "positive"]
            return self._answer(likes, now, limit=5) or "You haven't told me about your hobbies yet."

        if re.search(r"\bwhat (?:\w+ )?(?:do|did) i (?:usually )?(?:like|enjoy|love|prefer|drink|eat|play)\b|"
                     r"\bwhat (?:\w+ )?am i (?:fond|into)\b|\bwhat did i (?:tell|say)\b", t):
            asked = _words(t) - {"what", "do", "did", "i", "usually", "like", "enjoy", "love", "prefer", "drink",
                                 "eat", "play", "am", "fond", "of", "into", "tell", "say", "you", "the", "a"}
            cat = next((c for c, words in CATEGORY_WORDS.items() if asked & words), None)
            if cat is None and re.search(r"\bdrink\b", t):
                cat = "drink"
            if cat is None and re.search(r"\b(eat)\b", t):
                cat = "food"
            if cat is None and re.search(r"\bplay\b", t):
                cat = "sport"
            likes = [f for f in facts if f.key.split(":")[0] in ("likes", "prefers", "favorite")
                     and f.polarity == "positive"]
            if cat:
                hits = [f for f in likes if f.category == cat]
            elif asked:
                hits = [f for f in likes if asked & _words(f.value)]
            else:
                return self._answer(likes, now, limit=5) or "I don't have a record of that yet. You can tell me, and I'll remember."
            return self._answer(hits, now) or "I don't have a record of that yet. You can tell me, and I'll remember."
        return None

    def _answer(self, hits: list[StoredFact], now: datetime, limit: int = 3) -> Optional[str]:
        if not hits:
            return None
        hits = sorted(hits, key=lambda f: f.timestamp or datetime.min, reverse=True)[:limit]
        parts = [f"{_when(f.timestamp, now)} that {_to_second_person(f.statement)}" for f in hits]
        return "You told me " + "; and ".join(parts) + "."

    # ------------------------------------------------------------------
    # Fact persistence
    # ------------------------------------------------------------------

    def _repo(self):
        return getattr(self.db, "memory_repo", None)

    def _save_fact(self, memory_id: str, key: str, value: str, polarity: str, statement: str) -> None:
        repo = self._repo()
        if repo is None:
            raise RuntimeError("No memory repository available to store facts.")
        category = _category_of(value) or ""
        repo.save(RelevantMemory(
            memory_id=memory_id,
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.HIGH,
            title=f"User fact: {key}",
            summary=statement,
            timestamp=self.clock(),
            tags=[FACT_TAG, PREFERENCE_TAG, f"fact_key:{key}", f"fact_value:{value}", f"polarity:{polarity}",
                  "status:active", "source:user_provided", f"category:{category}"],
        ))

    def _mark_superseded(self, fact: StoredFact, by_id: str) -> None:
        repo = self._repo()
        mem = next((m for m in self._raw_fact_memories() if m.memory_id == fact.memory_id), None)
        if mem is None:
            return
        tags = [tg for tg in mem.tags if not tg.startswith("status:")] + ["status:superseded", f"superseded_by:{by_id}"]
        repo.save(dataclasses.replace(mem, tags=tags))

    def _raw_fact_memories(self) -> list[RelevantMemory]:
        repo = self._repo()
        if repo is None:
            return []
        if hasattr(repo, "find_explicit"):
            mems = repo.find_explicit(tags=[FACT_TAG])
        else:
            mems = [m for m in repo.find(tags=[FACT_TAG]) if not m.memory_id.startswith(("ep_", "sem_"))]
        return mems

    def all_facts(self) -> list[StoredFact]:
        facts = []
        for m in self._raw_fact_memories():
            tags = {tg.split(":", 1)[0]: tg.split(":", 1)[1] for tg in (m.tags or []) if ":" in tg}
            if "fact_key" not in tags:
                # Facts stored by older versions: free text, treated as an unkeyed positive statement.
                parsed = self._parse_statement(_norm(m.summary or ""))
                key, value, polarity = (parsed[0], parsed[1], parsed[2]) if parsed else (f"note:{m.memory_id}", m.summary or "", "positive")
                tags.update({"fact_key": key, "fact_value": value, "polarity": polarity})
            facts.append(StoredFact(
                memory_id=m.memory_id, key=tags["fact_key"], value=tags.get("fact_value", ""),
                polarity=tags.get("polarity", "positive"), statement=m.summary or "", timestamp=m.timestamp,
                status=tags.get("status", "active"), source=tags.get("source", "user_provided"),
                category=tags.get("category") or _category_of(tags.get("fact_value", "")),
            ))
        return facts

    def active_facts(self) -> list[StoredFact]:
        return [f for f in self.all_facts() if f.status == "active"]

    # ------------------------------------------------------------------
    # Episodes, visitors, searches, objects
    # ------------------------------------------------------------------

    def _timeline(self, raw: str, t: str, **_) -> Optional[str]:
        if not re.search(r"\bwhat did i do( today)?\b|\bmy timeline\b|\bwhat happened today\b|\bsummary of (my )?day\b", t):
            return None
        repo = getattr(self.db, "episode_repo", None)
        episodes = repo.get_episodes_for_today() if repo else []
        lines = []
        for ep in episodes[-5:]:
            # Utterances may contain apostrophes ("I'm tired"): match up to the separator.
            said = re.search(r"User said: '(.*?)'(?: \| System responded:|$)", ep.summary or "")
            what = f"you said \"{said.group(1)}\"" if said else (ep.summary or "")
            if what and not what.startswith("System:"):
                stamp = ep.timestamp.strftime("%I:%M %p").lstrip("0") if isinstance(ep.timestamp, datetime) else ""
                lines.append(f"{stamp} {what}".strip())
        if not lines:
            return "I haven't recorded anything for today yet."
        return "Here's what I noted today: " + "; ".join(lines) + "."

    def _visitors(self, raw: str, t: str, **_) -> Optional[str]:
        if not re.search(r"\bwho (visited|came by|came today|has visited|was here)\b", t):
            return None
        repo = getattr(self.db, "episode_repo", None)
        own = (self.get_preferred_name() or "").lower()
        visitors = [v for v in (repo.get_visitors_for_today() if repo else []) if v and v.lower() != own]
        if not visitors:
            return "I haven't recorded any visitors today."
        names = visitors[0] if len(visitors) == 1 else ", ".join(visitors[:-1]) + " and " + visitors[-1]
        return f"I recorded {names} today."

    _MED_WORDS = r"(pills?|medicines?|medications?|tablets?|meds|dose)"

    def _match_medications(self, t: str) -> list:
        if self.medications is None:
            return []
        schedules = self.medications.get_all_schedules()
        words = _words(t)
        named = [m for m in schedules if words & (_words(m.medication_name) - {"mg", "the", "my"})]
        if named:
            return named
        if re.search(rf"\b{self._MED_WORDS}\b", t):
            due = self.medications.get_missed_medications(now=self.clock())
            return due or (schedules if len(schedules) == 1 else [])
        return []

    def _medication_report(self, raw: str, t: str, **_) -> Optional[str]:
        if not re.search(r"^(?:yes,? )?i(?:'ve| have)? (?:just )?(?:took|taken|had) (?:my |the )?", t) or "?" in t:
            return None
        if not (re.search(rf"\b{self._MED_WORDS}\b", t) or self._match_medications(t)):
            return None
        meds = self._match_medications(t)
        if not meds:
            return ("Thank you for telling me. I don't have a schedule that matches, so I haven't "
                    "recorded it. A carer can add your schedule.")
        now = self.clock()
        for m in meds:
            self.medications.report_taken(m.med_id, source="user statement", when=now)
        names = " and ".join(m.medication_name for m in meds)
        return f"Thank you. I've noted that you told me you took your {names} at {now.strftime('%I:%M %p').lstrip('0')}."

    def _medication_question(self, raw: str, t: str, **_) -> Optional[str]:
        if not re.search(rf"\b(did|have) i (?:already )?(?:take|taken|had|have)\b.*\b{self._MED_WORDS}\b|"
                         rf"\bdid i take my\b", t):
            return None
        if self.medications is None or not self.medications.get_all_schedules():
            return "I don't have any medication schedule recorded, so I can't say. Please check with someone who helps you."
        meds = self._match_medications(t) or self.medications.get_all_schedules()
        now = self.clock()
        replies = []
        for m in meds:
            if self.medications.reported_taken_today(m.med_id, now):
                replies.append(f"you told me today that you took your {m.medication_name}")
            else:
                replies.append(f"I don't have a report that you took your {m.medication_name} today")
        return (replies[0][0].upper() + "; ".join(replies)[1:] +
                ". I can only go by what you tell me, so if you're unsure, check your pill organiser "
                "or ask someone who helps you.")

    def _appointment(self, raw: str, t: str, **_) -> Optional[str]:
        if not re.search(r"\b(appointment|appointments|doctor's visit|checkup|check-up)\b", t) or not re.search(r"\b(when|what|is|do i|have i|any)\b", t):
            return None
        upcoming = self.appointments.get_upcoming_appointments() if self.appointments else []
        if not upcoming:
            return "I don't have any appointments recorded. A family member or carer can add them for you."
        parts = [f"{a.title} {a.scheduled_time}" + (f" at {a.location}" if getattr(a, "location", "") else "")
                 for a in upcoming[:3]]
        return "Here's what I have recorded: " + "; ".join(parts) + "."

    def _last_search(self, raw: str, t: str, **_) -> Optional[str]:
        if not re.search(r"\bwhat (was|am) i (looking|searching) for\b", t):
            return None
        if self.search_history:
            return f"Earlier you were looking for your {self.search_history[-1]['object']}."
        return "I don't remember you looking for anything recently."

    def _object_location(self, raw: str, t: str, **_) -> Optional[str]:
        patterns = [
            r"\bwhere (?:is|are|'s|did i (?:leave|put)|have i (?:left|put)|could) (?:my |the |your )?([a-z ]{2,40}?)(?: go| be)?\??$",
            r"\b(?:have you seen|did you see|do you know where) (?:my |the )?([a-z ]{2,40}?)(?: is| are)?\??$",
            r"\b(?:i lost|i've lost|i have lost|i can't find|i cannot find|i can not find|find|looking for) (?:my |the )?([a-z ]{2,40}?)[.!?]?$",
        ]
        target = None
        for pat in patterns:
            m = re.search(pat, t)
            if m:
                target = re.sub(r"\b(again|now|please|today|anywhere)\b", "", m.group(1)).strip()
                break
        mentioned = [obj for obj in sorted(KNOWN_OBJECTS, key=len, reverse=True)
                     if re.search(rf"\b{re.escape(obj)}\b", t)]  # whole words: "hat" must not match "what"
        if not target and not mentioned:
            return None
        if not target:
            target = mentioned[0]
        if target in ("i", "you", "we"):
            return None
        if target in PRONOUNS:
            recent = self.search_history[-1] if self.search_history else None
            if recent and time.time() - recent["timestamp"] < 600:
                target = recent["object"]
            else:
                return "Which item do you mean? For example: where are my glasses?"

        self.search_history.append({"object": target, "timestamp": time.time()})
        now = self.clock()
        visual = self._visual_observation(target)
        obs = self._latest_observation(target)
        if visual is not None and (obs is None or visual[2] >= obs[2]):
            name, room, seen_at, spatial, confidence = visual
            where = f"{spatial} in the {room}" if spatial else f"in the {room}"
            if confidence < 0.5:
                return f"I'm not certain where your {name} is right now."
            if confidence < 0.8:
                return f"I think your {name} may still be {where}, but I'm not certain."
            reply = f"I last saw your {name} {where} {_age_phrase(seen_at, now)}."
        elif obs is not None:
            name, room, seen_at = obs
            reply = f"I last saw your {name} in the {room} {_age_phrase(seen_at, now)}."
        else:
            plural = target.endswith("s") and not target.endswith("ss")
            it, they = ("them", "they are") if plural else ("it", "it is")
            return f"I haven't seen your {target}, so I can't say where {they}. Where do you usually keep {it}?"
        if now - seen_at > timedelta(hours=6):
            reply += " It may have been moved since then."
        return reply

    def _visual_observation(self, target: str):
        if self.visual_memory is None:
            return None
        res = self.visual_memory.recall_object_location(target)
        entry = res.get("entry") if res.get("found") else None
        if entry is None:
            return None
        try:
            seen_at = datetime.fromisoformat(entry.timestamp)
        except (TypeError, ValueError):
            return None
        return entry.object_category, entry.room, seen_at, entry.spatial_description, entry.confidence

    def _latest_observation(self, target: str) -> Optional[tuple[str, str, datetime]]:
        repo = getattr(self.db, "object_repo", None)
        info = repo.search_object(target) if repo else None
        if not info or not info.get("last_seen"):
            return None
        try:
            seen_at = datetime.fromisoformat(info["last_seen"])
        except (TypeError, ValueError):
            return None
        return str(info.get("name", target)).replace("_", " ").lower(), info.get("room") or "an unknown room", seen_at
