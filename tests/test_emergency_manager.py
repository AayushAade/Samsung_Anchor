from src.clinical.clinical_models import EmergencyPriority
from src.clinical.emergency_manager import EmergencyManager


def test_emergency_manager_trigger_and_clear():
    mgr = EmergencyManager()
    state = mgr.get_current_state()
    assert state.active is False

    mgr.trigger_emergency("Fall Detected in Living Room", priority=EmergencyPriority.CRITICAL)
    state = mgr.get_current_state()
    assert state.active is True
    assert state.priority == EmergencyPriority.CRITICAL
    assert state.caregiver_notified is True

    mgr.clear_emergency()
    state = mgr.get_current_state()
    assert state.active is False
