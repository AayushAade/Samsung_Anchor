from src.clinical.clinical_models import MedicationSchedule
from src.clinical.medication_manager import MedicationManager


def test_medication_manager_operations():
    mgr = MedicationManager()
    all_meds = mgr.get_all_schedules()
    assert len(all_meds) >= 2

    missed = mgr.get_missed_medications()
    assert len(missed) >= 2

    # Mark donepezil taken
    res = mgr.mark_taken("MED-001")
    assert res is True
    assert len(mgr.get_missed_medications()) == len(missed) - 1
