from src.perception.activity_detector import ActivityDetector
from src.perception.sensor_models import ActivityType, RoomLocation


def test_activity_detector_inference():
    detector = ActivityDetector()

    # Living Room + Glasses -> Reading
    act1 = detector.infer_activity(RoomLocation.LIVING_ROOM, ["Reading Glasses"])
    assert act1 == ActivityType.READING

    # Kitchen + Medication -> Medication
    act2 = detector.infer_activity(RoomLocation.KITCHEN, ["Donepezil Medication Box"])
    assert act2 == ActivityType.MEDICATION

    # Bedroom -> Sleeping
    act3 = detector.infer_activity(RoomLocation.BEDROOM, [])
    assert act3 == ActivityType.SLEEPING
