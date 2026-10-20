"""
End-to-end conversation behaviour through the real CognitivePipeline.

Each case here was answered incorrectly before the conversational-memory
rework (see commit history); they are kept as regression tests.
"""

from __future__ import annotations

import pytest

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


@pytest.fixture
def pipeline():
    p = CognitivePipeline(MemoraDatabase(":memory:"))
    yield p
    p.shutdown()


def say(p, text):
    return p.process(user_speech=text, location="Living Room", return_dict=True)["speech_response"]


def test_statement_is_not_taken_as_a_name(pipeline):
    reply = say(pipeline, "I am tired today")
    assert "Today" not in reply and "registered your identity" not in reply
    assert pipeline.database.identity_repo.get_all() == []


def test_unrelated_fact_not_returned(pipeline):
    say(pipeline, "I like cricket")
    reply = say(pipeline, "What tea do I like?")
    assert "cricket" not in reply.lower()


def test_fact_round_trip_and_correction(pipeline):
    say(pipeline, "My daughter is Riya")
    assert "Riya" in say(pipeline, "Who is my daughter?")
    say(pipeline, "No, my daughter's name is Priya, not Riya")
    answer = say(pipeline, "Who is my daughter?")
    assert "Priya" in answer and "Riya" not in answer.replace("Priya", "")


def test_where_am_i_is_orientation_not_object_lookup(pipeline):
    reply = say(pipeline, "Where am I?")
    assert "object" not in reply.lower()
    assert "can't tell" in reply


def test_no_fabricated_object_locations(pipeline):
    for _ in range(3):  # simulated perception cycles must not create observations
        pipeline.process({})
    reply = say(pipeline, "Where are my reading glasses?")
    assert reply.startswith("I haven't seen your reading glasses")
    assert pipeline.database.object_repo.get_all_objects() == {}


def test_speech_never_echoed_back_as_a_greeting(pipeline):
    say(pipeline, "The weather is nice")
    reply = say(pipeline, "The garden looks lovely")
    assert "previously you were discussing" not in reply.lower()
    assert reply  # every spoken turn gets a reply


def test_no_placeholder_patient_name_outside_demo(pipeline):
    reply = say(pipeline, "Hello")
    assert "Eleanor" not in reply
    say(pipeline, "My name is Sid")
    assert "Sid" in say(pipeline, "Hello")


def test_fact_stored_once_per_statement(pipeline):
    say(pipeline, "I like green tea")
    assert len(pipeline.conversational_memory.all_facts()) == 1


def test_own_turns_are_not_visits_and_not_attributed_to_placeholder(pipeline):
    say(pipeline, "My name is Sid")
    say(pipeline, "I like tea")
    assert say(pipeline, "Who visited today?") == "I haven't recorded any visitors today."
    people = {ep.person for ep in pipeline.database.episode_repo.get_all_episodes()}
    assert "Eleanor" not in people
    pipeline.process({"face_id": "2", "name": "Riya", "relationship": "Daughter"})
    assert say(pipeline, "Who visited today?") == "I recorded Riya today."
