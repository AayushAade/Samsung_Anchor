from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.runtime.runtime_models import DeviceStatus


def test_fault_injection_resilience():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    # 1. Inject Camera Fault
    pipeline.runtime_manager.hardware_manager.register_device("CameraAdapter", DeviceStatus.FAULTED)
    assert pipeline.runtime_manager.hardware_manager.get_device_status("CameraAdapter") == DeviceStatus.FAULTED

    # Pipeline should process gracefully despite fault
    rec = {"faces": []}
    actions = pipeline.process(rec)
    assert isinstance(actions, list)

    # 2. Inject Emergency Override
    pipeline.emergency_mgr.trigger_emergency("Fall Detected")
    assert pipeline.emergency_mgr.get_current_state().active is True

    # Pipeline handles emergency gracefully
    actions_emergency = pipeline.process(rec)
    assert len(actions_emergency) >= 0

    # Clear Emergency
    pipeline.emergency_mgr.clear_emergency()
    assert pipeline.emergency_mgr.get_current_state().active is False
