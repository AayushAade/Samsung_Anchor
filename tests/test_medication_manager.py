from datetime import datetime

from src.clinical.clinical_models import MedicationSchedule
from src.clinical.medication_manager import MedicationManager


def test_medication_manager_operations():
    mgr = MedicationManager(seed_demo_data=True)
    all_meds = mgr.get_all_schedules()
    assert len(all_meds) >= 2

    evening = datetime.now().replace(hour=21, minute=0)
    missed = mgr.get_missed_medications(now=evening)
    assert len(missed) >= 2

    # Mark donepezil taken
    res = mgr.mark_taken("MED-001")
    assert res is True
    assert len(mgr.get_missed_medications(now=evening)) == len(missed) - 1


def test_no_medications_unless_configured():
    """Real users must never be reminded about fictional demo prescriptions."""
    mgr = MedicationManager()
    assert mgr.get_all_schedules() == []
    assert mgr.get_missed_medications() == []


def test_dose_not_missed_before_scheduled_time_plus_grace():
    mgr = MedicationManager(grace_minutes=30)
    mgr.add_medication(MedicationSchedule(med_id="M1", medication_name="Test med", dose="1",
                                          scheduled_time="06:00 PM", instructions=""))
    day = datetime.now()
    assert mgr.get_missed_medications(now=day.replace(hour=9, minute=0)) == []
    assert mgr.get_missed_medications(now=day.replace(hour=18, minute=15)) == []
    assert [m.med_id for m in mgr.get_missed_medications(now=day.replace(hour=18, minute=31))] == ["M1"]
