from datetime import datetime
from typing import List, Dict
from src.perception.sensor_models import DetectedObject, RoomLocation


class ObjectDetector:
    """
    Household object detector tracking essential personal & medical items.
    """

    def __init__(self) -> None:
        self._objects: Dict[str, DetectedObject] = {}

        # Seed essential objects
        now_str = datetime.now().strftime("%H:%M:%S")
        self._objects["Reading Glasses"] = DetectedObject(
            object_name="Reading Glasses",
            location=RoomLocation.LIVING_ROOM,
            confidence=0.92,
            last_seen=now_str,
            is_moving=False,
        )
        self._objects["Water Bottle"] = DetectedObject(
            object_name="Water Bottle",
            location=RoomLocation.LIVING_ROOM,
            confidence=0.95,
            last_seen=now_str,
            is_moving=False,
        )
        self._objects["Donepezil Medication Box"] = DetectedObject(
            object_name="Donepezil Medication Box",
            location=RoomLocation.KITCHEN,
            confidence=0.98,
            last_seen=now_str,
            is_moving=False,
        )

    def detect_objects_for_room(self, room: RoomLocation) -> List[DetectedObject]:
        return [obj for obj in self._objects.values() if obj.location == room]

    def add_object(self, obj: DetectedObject) -> None:
        self._objects[obj.object_name] = obj

    def get_all_objects(self) -> List[DetectedObject]:
        return list(self._objects.values())
