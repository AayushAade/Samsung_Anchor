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


def test_relation_fact_and_correction_supersedes_with_history(mem):
    mem.respond("My daughter is Riya")
    assert mem.respond("Who is my daughter?") == "You told me today that your daughter is Riya."
    reply = mem.respond("My daughter's name is Priya")
    assert "updated" in reply and "Riya" in reply
    assert mem.respond("Who is my daughter?") == "You told me today that your daughter's name is Priya."
    statuses = sorted(f.status for f in mem.all_facts())
    assert statuses == ["active", "superseded"], "old fact is kept for history, not deleted"


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
    mem.db.log_object("reading_glasses", 1.0, 2.0, "Living Room")
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
