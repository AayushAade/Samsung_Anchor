from src.runtime.sensor_bus import SensorBus
from src.runtime.runtime_models import SensorEvent, SensorEventType


def test_sensor_bus_pub_sub():
    bus = SensorBus()
    received = []

    def callback(evt: SensorEvent):
        received.append(evt)

    bus.subscribe(SensorEventType.CAMERA_FRAME, callback)

    event = SensorEvent(event_type=SensorEventType.CAMERA_FRAME, source_device="CameraAdapter")
    bus.publish(event)

    assert len(received) == 1
    assert received[0].source_device == "CameraAdapter"
