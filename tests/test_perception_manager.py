from src.perception.perception_manager import PerceptionManager
from src.perception.sensor_models import RoomLocation


def test_perception_manager_cycle():
    mgr = PerceptionManager()
    rec = {
        "faces": [
            {"face_id": "Face_1", "name": "Sarah", "confidence": 0.95}
        ]
    }

    ctx = mgr.process_cycle(rec)
    assert ctx is not None
    assert ctx.current_room == RoomLocation.LIVING_ROOM
    assert len(ctx.detected_faces) == 1
    assert ctx.detected_faces[0].name == "Sarah"
    assert ctx.fps > 0
