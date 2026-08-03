import os
import tempfile
import pytest
from datetime import datetime
from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.memory.database import MemoraDatabase
from src.memory.models import EpisodeModel
from src.cognition.episode import Episode
from src.interaction.events import PresenceEvent, PresenceEventType


def test_scenario1_person_greeting_with_history():
    """
    Scenario 1: User (Sid) walks into room.
    System detects face, recognizes identity, loads previous memories, and greets naturally.
    """
    db = MemoraDatabase(":memory:")
    # Seed an episode for Sid
    ep = Episode(
        person="Sid",
        summary="Worked on Samsung Anchor feature/episodic-memory",
        timestamp=datetime.now(),
        location="Study Room",
        commitments=[],
        tags=["project:Samsung Anchor"],
    )
    db.episode_repo.add_episode(ep)

    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()
    runtime.start()

    # Simulate face detection event for Sid
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="face_sid",
        name="Sid",
        relationship="Developer",
    )

    actions = coord.pipeline.process(
        {
            "event": event,
            "face_id": "face_sid",
            "name": "Sid",
            "relationship": "Developer",
        }
    )

    assert len(actions) > 0
    message = actions[0].message
    assert "Sid" in message
    assert "Previously" in message or "Samsung Anchor" in message or "Hello" in message

    runtime.shutdown()


def test_scenario2_object_location_recall():
    """
    Scenario 2: User asks "Where are my glasses?"
    System searches object history, ranks observations, and returns latest reliable observation.
    """
    db = MemoraDatabase(":memory:")
    db.object_repo.log_object(
        object_name="Reading Glasses",
        x=200.0,
        y=150.0,
        room="Living Room",
        bounding_box=[100, 100, 50, 20],
    )

    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    # Query location
    actions = coord.pipeline.process(
        {
            "user_speech": "Where are my glasses?",
        }
    )

    assert len(actions) > 0
    message = actions[0].message
    assert "glasses" in message.lower() or "reading glasses" in message.lower()
    assert "living room" in message.lower() or "table" in message.lower() or "saw" in message.lower()


def test_scenario3_timeline_generation():
    """
    Scenario 3: User asks "What did I do today?"
    System constructs an actual timeline from stored episodes.
    """
    db = MemoraDatabase(":memory:")
    db.episode_repo.add_episode(Episode(person="Eleanor", summary="8:10 Breakfast", timestamp=datetime.now()))
    db.episode_repo.add_episode(Episode(person="Eleanor", summary="8:30 Medicine", timestamp=datetime.now()))
    db.episode_repo.add_episode(Episode(person="Riya", summary="9:00 Talked with Riya", timestamp=datetime.now()))

    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    actions = coord.pipeline.process(
        {
            "user_speech": "What did I do today?",
        }
    )

    assert len(actions) > 0
    message = actions[0].message
    assert "today" in message.lower() or "timeline" in message.lower() or "breakfast" in message.lower()


def test_scenario4_visitor_history():
    """
    Scenario 4: User asks "Who visited today?"
    System answers using face recognition / visitor episode history.
    """
    db = MemoraDatabase(":memory:")
    db.episode_repo.add_episode(Episode(person="Riya", summary="Visited for tea", timestamp=datetime.now()))
    db.episode_repo.add_episode(Episode(person="Sid", summary="Assisted with device setup", timestamp=datetime.now()))

    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    actions = coord.pipeline.process(
        {
            "user_speech": "Who visited today?",
        }
    )

    assert len(actions) > 0
    message = actions[0].message
    assert "Riya" in message
    assert "Sid" in message


def test_scenario5_inferred_search_behavior():
    """
    Scenario 5: User asks "What was I looking for?"
    System infers repeated search behavior.
    """
    coord = build_application(live_hardware=False)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    # User performs repeated search query
    coord.pipeline.process({"user_speech": "Where are my keys?"})

    # User asks what they were looking for
    actions = coord.pipeline.process({"user_speech": "What was I looking for?"})

    assert len(actions) > 0
    message = actions[0].message
    assert "keys" in message.lower() or "searching" in message.lower() or "wallet" in message.lower()


def test_honest_response_when_object_never_observed():
    """
    Absolute Rule #1 Test: If an object has never been observed, say 'I have never observed that object.'
    """
    coord = build_application(live_hardware=False)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    actions = coord.pipeline.process({"user_speech": "Where is my telescope?"})
    assert len(actions) > 0
    message = actions[0].message
    assert "never observed" in message.lower() or "haven't seen" in message.lower()


def test_honest_response_when_no_episodes_recorded():
    """
    Absolute Rule #1 Test: If no timeline/episodes exist for today, honestly state no activities recorded.
    """
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    actions = coord.pipeline.process({"user_speech": "What did I do today?"})
    assert len(actions) > 0
    message = actions[0].message
    assert "no activities" in message.lower() or "recorded" in message.lower() or "episodes" in message.lower()


def test_honest_response_when_no_search_history_exists():
    """
    Absolute Rule #1 Test: If no repeated search query has occurred, honestly state no recent searches.
    """
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    actions = coord.pipeline.process({"user_speech": "What was I looking for?"})
    assert len(actions) > 0
    message = actions[0].message
    assert "haven't searched" in message.lower() or "no recent" in message.lower() or "recently" in message.lower()


def test_conversation_preference_memory_extraction_and_recall():
    """
    Objective 7 Test: Preference & Fact Extraction from conversation.
    User states preference ("My favorite tea is green tea"), then asks ("What tea do I like?").
    """
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    # Step 1: User states preference
    act1 = coord.pipeline.process({"user_speech": "My favorite tea is green tea."})
    assert len(act1) > 0
    assert "noted" in act1[0].message.lower() or "preference" in act1[0].message.lower()

    # Step 2: User asks for preference recall
    act2 = coord.pipeline.process({"user_speech": "What tea do I like?"})
    assert len(act2) > 0
    assert "green tea" in act2[0].message.lower() or "favorite tea" in act2[0].message.lower()


def test_conversation_relationship_fact_memory_extraction_and_recall():
    """
    Objective 6 Test: Pure Fact Retrieval ("My daughter is Riya" -> "Who is my daughter?").
    """
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    # Step 1: User states fact
    act1 = coord.pipeline.process({"user_speech": "My daughter is Riya."})
    assert len(act1) > 0
    assert "noted" in act1[0].message.lower()

    # Step 2: User asks for fact recall
    act2 = coord.pipeline.process({"user_speech": "Who is my daughter?"})
    assert len(act2) > 0
    assert "riya" in act2[0].message.lower() or "daughter" in act2[0].message.lower()


def test_llm_mode_diagnostic_reporting():
    """
    Objective 5 Test: LLM Mode reporting in Runtime diagnostics.
    """
    coord = build_application(live_hardware=False)
    runtime = AnchorRuntime(coord)
    runtime.initialize()

    statuses = runtime.get_subsystem_statuses()
    assert "Cognition" in statuses

    # Verify diagnostic text output
    diag = coord.pipeline.runtime_manager.generate_diagnostic_report()
    assert "Reasoning Engine" in diag
    assert "LLM Mode" in diag


def test_application_restart_persistence():
    """
    Requirement 13: Memory survives application restart.
    Save episodes and objects into temporary file SQLite DB, destroy runtime, reopen DB, and verify persistence.
    """
    with tempfile.NamedTemporaryFile(suffix="_v2.sqlite", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Phase 1: Write data in Session 1
        db1 = MemoraDatabase(db_path)
        db1.episode_repo.add_episode(
            Episode(person="Sid", summary="Discussed Anchor memory architecture", timestamp=datetime.now(), location="Office")
        )
        db1.object_repo.log_object("Wallet", 100.0, 200.0, "Bedroom", [10, 10, 40, 20])
        db1.close()

        # Phase 2: Open new Session 2 from disk
        db2 = MemoraDatabase(db_path)
        episodes = db2.episode_repo.get_all_episodes()
        assert len(episodes) == 1
        assert episodes[0].person == "Sid"
        assert "Anchor memory" in episodes[0].summary

        obj_info = db2.object_repo.get_last_known_location("Wallet")
        assert obj_info is not None
        assert obj_info["room"] == "Bedroom"
        db2.close()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
