from src.cognition.relationships.manager import RelationshipManager
from src.cognition.relationships.models import RelationshipProfile


def test_relationship_manager_get_seeded_profile():
    manager = RelationshipManager()
    profile = manager.get_profile("Face_1", name="Sarah", relationship="Daughter")

    assert profile is not None
    assert profile.name == "Sarah"
    assert profile.relationship == "Daughter"
    assert len(profile.shared_memories) > 0
    assert len(profile.important_dates) > 0


def test_relationship_manager_dynamic_fallback():
    manager = RelationshipManager()
    profile = manager.get_profile("Face_99", name="Bob", relationship="Neighbor")

    assert profile is not None
    assert profile.name == "Bob"
    assert profile.relationship == "Neighbor"
    assert profile.closeness_score == 0.85


def test_relationship_manager_register_profile():
    manager = RelationshipManager()
    new_profile = RelationshipProfile(
        person_id="Face_42",
        name="Grandson Tim",
        relationship="Grandson",
        preferred_greeting="Hi Timmy!",
    )
    manager.register_profile(new_profile)

    fetched = manager.get_profile("Face_42")
    assert fetched is not None
    assert fetched.name == "Grandson Tim"
    assert fetched.preferred_greeting == "Hi Timmy!"
