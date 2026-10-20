"""
Deterministic detection of potentially urgent situations in user speech.

This runs before any memory lookup, reasoning, or cloud call so that a
statement such as "I fell" or "I can't breathe" is never answered with a
memory recall, a medication reminder, or false reassurance.

Design notes
------------
- Rule-based and conservative: a false alarm costs a gentle prompt to get help;
  a miss can cost far more. Only well-known benign idioms are excluded.
- MEMORA has no channel to contact caregivers or emergency services, so the
  guidance never claims that anyone has been notified. It directs the user to
  human help.
- This is not a clinically validated triage instrument.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UrgentConcernType(Enum):
    BREATHING = "breathing difficulty"
    CHEST_PAIN = "chest pain"
    FALL_OR_INJURY = "fall or injury"
    BLEEDING = "bleeding"
    STROKE_SIGNS = "possible stroke signs"
    MEDICATION_OVERDOSE = "possible medication overdose"
    SELF_HARM = "self-harm"
    UNRESPONSIVE_OR_FAINTING = "fainting or collapse"
    HELP_REQUEST = "request for help"


@dataclass(frozen=True)
class UrgentConcern:
    concern_type: UrgentConcernType
    matched_text: str


# Patterns are matched against normalised lowercase text (see _normalise).
_PATTERNS: list[tuple[UrgentConcernType, str]] = [
    (UrgentConcernType.SELF_HARM,
     r"\b(kill myself|end my life|want to die|hurt myself|suicid\w*)\b"),
    (UrgentConcernType.BREATHING,
     r"\b(cannot breathe|can not breathe|could not breathe|hard to breathe|trouble breathing|"
     r"difficulty breathing|short of breath|choking|struggling to breathe)\b"),
    (UrgentConcernType.CHEST_PAIN,
     r"\b(chest (pain|hurts|is hurting|feels tight|tightness)|pain in my chest|heart attack)\b"),
    (UrgentConcernType.STROKE_SIGNS,
     r"\b(face (is )?drooping|cannot move my (arm|leg|face)|can not move my (arm|leg|face)|"
     r"slurr\w* (my )?(speech|words)|numb on one side|stroke)\b"),
    (UrgentConcernType.UNRESPONSIVE_OR_FAINTING,
     r"\b(faint\w*|passed out|blacked out|collapsed|going to pass out)\b"),
    (UrgentConcernType.FALL_OR_INJURY,
     r"\b((i|he|she|they|we|my \w+|mom|mum|dad) (just )?(have |has )?(fell|fallen)|fell down|fallen down|tripped|"
     r"cannot get up|can not get up|i am hurt|i hurt my|i am injured|broke my|broken (arm|leg|hip|wrist))\b"),
    (UrgentConcernType.BLEEDING,
     r"\b(bleeding|blood everywhere|i cut myself|deep cut)\b"),
    (UrgentConcernType.MEDICATION_OVERDOSE,
     r"\b(too many (pills|tablets|medicines?)|took (all )?(my|the) pills twice|double dose|overdose\w*|"
     r"took the wrong (pills|medicine|medication))\b"),
    (UrgentConcernType.HELP_REQUEST,
     r"\b(help me|call (an )?ambulance|call 911|call 999|call 112|emergency|somebody help|someone help)\b"),
]

# Benign idioms that would otherwise match.
_EXCLUSIONS = re.compile(
    r"\b(fell asleep|fell in love|fell for|fall asleep|faint (smell|sound|light|idea|memory)|"
    r"emergency (contact|number)s? (is|are)|help me (find|remember|with)|"
    r"help me (look|search))\b"
)

_CONTRACTIONS = {
    "can't": "cannot", "cant": "cannot", "couldn't": "could not", "i'm": "i am", "im ": "i am ",
    "i've": "i have", "won't": "will not", "don't": "do not",
}


def _normalise(text: str) -> str:
    t = text.lower().replace("’", "'")
    for k, v in _CONTRACTIONS.items():
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


def detect_urgent_concern(text: Optional[str]) -> Optional[UrgentConcern]:
    """Return the most serious urgent concern expressed in text, or None."""
    if not text or not text.strip():
        return None
    t = _normalise(text)
    benign = _EXCLUSIONS.sub(" ", t)
    for concern_type, pattern in _PATTERNS:
        m = re.search(pattern, benign)
        if m:
            return UrgentConcern(concern_type=concern_type, matched_text=m.group(0))
    return None


def urgent_guidance(concern: UrgentConcern, name: Optional[str] = None,
                    emergency_number: Optional[str] = None,
                    trusted_contact: Optional[str] = None) -> str:
    """
    Calm, short guidance that directs the user to human help.

    Never states or implies that MEMORA has contacted anyone.
    """
    who = f"{name}, " if name else ""
    call = f"call {emergency_number}" if emergency_number else "call your local emergency number"
    also = f" You can also call {trusted_contact}." if trusted_contact else ""
    if concern.concern_type == UrgentConcernType.SELF_HARM:
        return (f"{who}I'm really glad you told me. You deserve support right now. "
                f"Please {call}, or a crisis line, or tell someone near you. "
                f"I can't contact anyone myself.{also}")
    if concern.concern_type == UrgentConcernType.HELP_REQUEST:
        return (f"{who}I hear that you need help. If you are hurt or unwell, please {call} "
                "or press your help button, or call out to someone nearby. "
                f"I can't contact anyone myself.{also}")
    return (f"{who}that sounds serious. Please {call} now, or press your help button, "
            f"or call out to someone nearby. I can't contact anyone myself.{also}")
