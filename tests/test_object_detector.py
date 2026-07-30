from src.perception.object_detector import ObjectDetector
from src.perception.sensor_models import DetectedObject, RoomLocation


def test_object_detector_room_filtering():
    detector = ObjectDetector()
    living_objs = detector.detect_objects_for_room(RoomLocation.LIVING_ROOM)

    assert len(living_objs) >= 2
    names = [o.object_name for o in living_objs]
    assert "Reading Glasses" in names

    kitchen_objs = detector.detect_objects_for_room(RoomLocation.KITCHEN)
    assert any("Medication" in o.object_name for o in kitchen_objs)
