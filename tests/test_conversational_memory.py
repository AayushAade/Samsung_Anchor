"""
Conversational memory correctness: facts, corrections, recall relevance,
names, orientation, and object "last seen" answers.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.cognition.conversational_memory import ConversationalMemory
from src.memory.database import MemoraDatabase


class Clock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock():
    return Clock(datetime(2026, 10, 20, 15, 20))


@pytest.fixture
def mem(clock):
    return ConversationalMemory(MemoraDatabase(":memory:"), clock=clock)


def test_stores_fact_and_answers_with_attribution(mem):
    assert mem.respond("I like green tea") == "I'll remember that you like green tea."
    assert mem.respond("What tea do I like?") == "You told me today that you like green tea."


def test_unrelated_fact_is_not_offered_as_an_answer(mem):
    mem.respond("I like cricket")
    reply = mem.respond("What tea do I like?")
    assert "cricket" not in reply
    assert "don't have a record" in reply


def test_category_questions(mem):
    mem.respond("I like cricket")
    mem.respond("I love coffee")
    assert "cricket" in mem.respond("What sports do I enjoy?")
    assert "coffee" not in mem.respond("What sports do I enjoy?")
    assert "coffee" in mem.respond("What do I usually drink?")


def test_second_daughter_is_kept_and_conflict_surfaced(mem):
    """People can have more than one daughter: never silently replace one with another."""
    mem.respond("My daughter is Riya")
    assert mem.respond("Who is my daughter?") == "You told me today that your daughter is Riya."
    reply = mem.respond("My daughter's name is Priya")
    assert "more than one daughter" in reply and "Riya" in reply and "Priya" in reply
    answer = mem.respond("Who is my daughter?")
    assert answer.startswith("You've told me about more than one daughter") and "Riya" in answer and "Priya" in answer


def test_explicit_correction_retracts_with_history(mem):
    mem.respond("My daughter is Riya")
    mem.respond("My daughter is Priya")
    assert "won't say your daughter is Riya" in mem.respond("My daughter is not Riya")
    assert mem.respond("Who is my daughter?") == "You told me today that your daughter is Priya."
    assert sorted(f.status for f in mem.all_facts()) == ["active", "retracted"], "history is kept"


def test_combined_correction_and_single_valued_relations(mem):
    mem.respond("My son is Arjun")
    reply = mem.respond("No, my son's name is Leo, not Arjun")
    assert "won't say your son is Arjun" in reply and "your son is Leo" in reply
    assert mem.respond("Who is my son?") == "You told me today that your son is Leo."
    mem.respond("My wife is Meera")
    assert "updated" in mem.respond("My wife is Anita")


def test_negated_relation_is_never_stored_as_a_name(mem):
    mem.respond("My daughter is not Riya")
    assert all("not" not in f.value for f in mem.all_facts())


def test_have_two_relations(mem):
    assert mem.respond("I have two daughters, Riya and Priya") == "I'll remember that your daughters are Riya and Priya."
    assert "more than one daughter" in mem.respond("Who is my daughter?")


def test_pronouns_are_not_stored_or_looked_up_blindly(mem):
    assert "What do you mean by 'it'" in mem.respond("I like it")
    assert mem.all_facts() == []
    assert mem.respond("Have you seen them?").startswith("Which item do you mean?")
    mem.respond("Where are my keys?")
    assert "keys" in mem.respond("Have you seen them?")


def test_forget_and_name_controls(mem):
    mem.respond("I like tea")
    assert "won't use that any more" in mem.respond("Forget that I like tea")
    assert "tea" not in (mem.respond("What do I like?") or "")
    assert "/delete-all" in mem.respond("Forget everything")
    assert "couldn't find that" in mem.respond("Forget that I like opera")
    assert mem.respond("What's my name?").startswith("You haven't told me your name")
    mem.respond("My name is Sid")
    assert mem.respond("Who am I?") == "You told me your name is Sid."
    mem.respond("My name is not Sid")
    assert not mem.get_preferred_name()


def test_negation_supersedes_positive_preference(mem):
    mem.respond("I like milk")
    reply = mem.respond("I don't like milk anymore")
    assert "updated" in reply
    answer = mem.respond("Do I like milk?")
    assert "don't like milk" in answer
    assert answer.count("milk") == 1


def test_duplicate_statement_is_not_stored_twice(mem):
    mem.respond("I like tea")
    assert mem.respond("I like tea").startswith("I already have that noted")
    assert len(mem.all_facts()) == 1


def test_unknown_answers_are_honest(mem):
    assert "don't know who your son is" in mem.respond("Who is my son?")
    assert "haven't told me your favorite color" in mem.respond("What is my favorite color?")


def test_facts_survive_restart(tmp_path, clock):
    path = str(tmp_path / "facts.sqlite")
    ConversationalMemory(MemoraDatabase(path), clock=clock).respond("My favourite song is Moon River")
    reloaded = ConversationalMemory(MemoraDatabase(path), clock=clock)
    assert reloaded.respond("What's my favorite song?") == "You told me today that your favourite song is Moon River."


def test_attribution_uses_relative_dates(mem, clock):
    mem.respond("I like jazz")
    clock.now += timedelta(days=1)
    assert mem.respond("Do I like jazz?") == "You told me yesterday that you like jazz."
    clock.now += timedelta(days=5)
    assert mem.respond("Do I like jazz?") == "You told me on October 20 that you like jazz."


@pytest.mark.parametrize("utterance", ["I am tired today", "I'm tired", "i'm fine", "I am going home",
                                       "i am sid", "I'm scared"])
def test_statements_are_not_mistaken_for_names(mem, utterance):
    reply = mem.respond(utterance)
    assert not (reply or "").startswith("Nice to meet you")
    assert "Sid" not in (reply or "") and "Today" not in (reply or "")
    assert mem.get_preferred_name() is None


@pytest.mark.parametrize("utterance", ["My name is Sid", "my name is sid", "Call me Sid", "I'm Sid", "Hi, I am Sid."])
def test_explicit_introductions_set_preferred_name(mem, utterance):
    assert mem.respond(utterance).startswith("Nice to meet you, Sid")
    assert mem.get_preferred_name() == "Sid"


def test_introduction_never_renames_an_unrelated_identity(mem):
    import numpy as np
    other = mem.db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    mem.db.bind_name(other, "Riya", "Daughter")
    mem.respond("My name is Sid")
    assert mem.db.get_identity(other)["display_name"] == "Riya"


def test_introduction_with_recognised_face_labels_that_identity_only(mem):
    import numpy as np
    face = mem.db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    mem.respond("I'm Riya", face_id=face)
    ident = mem.db.get_identity(face)
    assert ident["display_name"] == "Riya" and ident["relationship"] is None


def test_orientation_uses_clock(mem):
    assert mem.respond("What time is it?") == "It's 3:20 PM."
    assert mem.respond("What day is it?") == "Today is Tuesday, October 20, 2026."
    assert "MEMORA" in mem.respond("Who are you?")
    where = mem.respond("Where am I?")
    assert "can't tell" in where and "object" not in where


def test_object_never_seen_is_reported_honestly(mem):
    reply = mem.respond("Where are my keys?")
    assert reply == "I haven't seen your keys, so I can't say where they are. Where do you usually keep them?"


def test_object_last_seen_with_age_and_staleness(mem, clock):
    mem.db.log_object("reading_glasses", 1.0, 2.0, "Living Room", source="REAL_CAMERA")
    seen = datetime.fromisoformat(mem.db.get_last_known_location("reading_glasses")["last_seen"])
    clock.now = seen + timedelta(minutes=20)
    assert mem.respond("Where are my glasses?") == "I last saw your reading glasses in the Living Room about 20 minutes ago."
    clock.now = seen + timedelta(days=1, hours=1)
    reply = mem.respond("Have you seen my reading glasses?")
    assert reply.startswith("I last saw your reading glasses in the Living Room yesterday")
    assert "may have been moved" in reply


def test_lost_item_phrasing_and_last_search(mem):
    assert mem.respond("I lost my wallet").startswith("I haven't seen your wallet")
    assert mem.respond("What was I looking for?") == "Earlier you were looking for your wallet."


def test_urgent_statements_are_left_to_safety_layer(mem):
    assert mem.respond("I fell and I like tea") is None
    assert mem.all_facts() == []


def test_feelings_get_empathetic_reply(mem):
    assert "rest" in mem.respond("I am tired today")


def test_restatement_drops_trailing_time_words(mem):
    mem.respond("I prefer tea")
    assert mem.respond("I prefer coffee now").endswith("Now I have: you prefer coffee.")


def test_unmatched_speech_returns_none(mem):
    assert mem.respond("The weather is nice") is None


def test_observation_provenance_is_stated(mem, clock):
    mem.db.log_object("keys", 0, 0, "Hall", source="SIMULATED_CAMERA", when=clock.now)
    assert mem.respond("Where are my keys?").endswith("(in a simulation, not a real camera).")
    mem.db.log_object("wallet", 0, 0, "Kitchen", when=clock.now)  # legacy: no source recorded
    reply = mem.respond("Where is my wallet?")
    assert reply.startswith("I have an older note that your wallet was in the Kitchen")
    assert "don't know how it was recorded" in reply


@pytest.mark.parametrize("correction", [
    "Actually my daughter is Priya", "Actually, my daughter's name is Priya", "No, my daughter is Priya",
    "no my daughter is Priya", "Sorry, my daughter is called Priya", "I mean, my daughter is Priya"])
def test_spoken_correction_replaces_single_earlier_name(mem, correction):
    """Found by the end-to-end CLI journey: a leading 'Actually' made the correction unrecognised."""
    mem.respond("My daughter is Riya")
    reply = mem.respond(correction)
    assert "updated" in reply and "Riya" in reply
    answer = mem.respond("Who is my daughter?")
    assert "Priya" in answer and "Riya" not in answer


def test_correction_word_does_not_drop_one_of_several_names(mem):
    mem.respond("I have two daughters, Riya and Asha")
    reply = mem.respond("Actually my daughter is Priya")
    assert "more than one daughter" in reply
    answer = mem.respond("Who is my daughter?")
    assert all(n in answer for n in ("Riya", "Asha", "Priya"))


@pytest.mark.parametrize("said, expected", [
    ("Actually I like green tea", "you like green tea"), ("Oh, I like coffee", "you like coffee"),
    ("Well, my son is Leo", "your son is Leo"), ("Actually my name is Asha", "Asha")])
def test_leading_filler_words_do_not_hide_the_statement(mem, said, expected):
    assert expected in (mem.respond(said) or "")


@pytest.mark.parametrize("said", ["No", "Actually", "Sorry", "Wait for me"])
def test_bare_lead_words_are_not_treated_as_statements(mem, said):
    mem.respond("My daughter is Riya")
    mem.respond(said)
    assert "Riya" in mem.respond("Who is my daughter?")


def test_person_reported_location_is_remembered_and_updated(mem, clock):
    """Found in review: 'I put my keys in the drawer' was ignored, and MEMORA kept asking
    'Where do you usually keep them?' while ignoring the answer."""
    assert "you put your keys in the drawer" in mem.respond("I put my keys in the drawer")
    assert mem.respond("Where are my keys?") == "You told me today that you put your keys in the drawer."
    assert "updated" in mem.respond("Actually my keys are on the kitchen table")
    assert mem.respond("Where did I leave my key?") == "You told me today that your keys are on the kitchen table."
    clock.now += timedelta(hours=8)
    assert mem.respond("Have you seen my keys?").endswith("It may have been moved since then.")


def test_reported_location_and_camera_sighting_are_both_stated_newest_first(mem, clock):
    mem.db.object_repo.log_object("keys", 0.5, 0.5, "Kitchen", source="SIMULATED_CAMERA", when=clock.now)
    clock.now += timedelta(minutes=30)
    mem.respond("I put my keys in the drawer")
    reply = mem.respond("Where are my keys?")
    assert reply.startswith("You told me today that you put your keys in the drawer.")
    assert "I last saw your keys in the Kitchen" in reply and "simulation" in reply


@pytest.mark.parametrize("said", ["My son is in the garden", "My daughter is at work", "My son is coming later"])
def test_where_a_relative_is_is_not_stored_as_their_name(mem, said):
    mem.respond(said)
    assert "don't know who" in mem.respond(f"Who is my {said.split()[1]}?")


@pytest.mark.parametrize("said, expected", [
    ("Turn off the stove", "can't control anything in your home"),
    ("Lock the front door", "can't control anything in your home"),
    ("Book a doctor's appointment", "can't book or cancel appointments"),
    ("Remind me to call Riya at 5pm", "nothing has been set"),
    ("Set an alarm for 7am", "nothing has been set")])
def test_requests_for_actions_memora_cannot_take_say_nothing_was_done(mem, said, expected):
    """Found in review: these got 'I'm not sure I understood' or, for 'book', an object lookup."""
    assert expected in mem.respond(said)


def test_remind_me_who_is_a_recall_question(mem):
    mem.respond("My daughter is Riya")
    assert "Riya" in mem.respond("Remind me who my daughter is")
    assert "Riya" in mem.respond("Can you remind me what my daughter's name is?")
