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


def test_perception_manager_camera_adapter_and_sensor_bus():
    from src.runtime.camera_adapter import SimulatedCameraAdapter
    from src.runtime.sensor_bus import SensorBus
    from src.runtime.runtime_models import SensorEventType

    bus = SensorBus()
    cam = SimulatedCameraAdapter("TestCam")
    cam.initialize()

    received_events = []
    bus.subscribe(SensorEventType.CAMERA_FRAME, lambda e: received_events.append(e))

    mgr = PerceptionManager()
    mgr.camera_pipeline.set_camera_adapter(cam)
    mgr.camera_pipeline.set_sensor_bus(bus)

    ctx = mgr.process_cycle()
    assert ctx is not None
    assert len(received_events) == 1
    assert received_events[0].source_device == "TestCam"
    assert received_events[0].data["frame_id"] == 1

