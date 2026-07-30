from src.perception.room_tracker import RoomTracker
from src.perception.sensor_models import RoomLocation


def test_room_tracker_transitions():
    tracker = RoomTracker(RoomLocation.LIVING_ROOM)
    assert tracker.get_current_room() == RoomLocation.LIVING_ROOM

    tracker.set_room(RoomLocation.KITCHEN)
    assert tracker.get_current_room() == RoomLocation.KITCHEN

    history = tracker.get_room_history()
    assert len(history) >= 2
