from typing import List, Any
from src.perception.sensor_models import ActivityType, RoomLocation


class ActivityDetector:
    """
    Deterministic human activity recognition engine.
    """

    def __init__(self, initial_activity: ActivityType = ActivityType.SITTING) -> None:
        self._current_activity = initial_activity

    def infer_activity(self, room: RoomLocation, objects_present: List[str] = None, face_present: bool = True) -> ActivityType:
        objs = [o.lower() for o in (objects_present or [])]

        if "fall" in objs or "floor" in objs:
            self._current_activity = ActivityType.FALLEN
        elif room == RoomLocation.KITCHEN:
            if "medication" in " ".join(objs):
                self._current_activity = ActivityType.MEDICATION
            else:
                self._current_activity = ActivityType.EATING
        elif room == RoomLocation.BEDROOM:
            self._current_activity = ActivityType.SLEEPING
        elif "glasses" in " ".join(objs) or "book" in " ".join(objs):
            self._current_activity = ActivityType.READING
        else:
            self._current_activity = ActivityType.SITTING

        return self._current_activity

    def set_activity(self, activity: ActivityType) -> ActivityType:
        self._current_activity = activity
        return self._current_activity

    def get_current_activity(self) -> ActivityType:
        return self._current_activity
