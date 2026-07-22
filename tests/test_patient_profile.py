from src.clinical.patient_profile import PatientProfileManager


def test_patient_profile_defaults():
    mgr = PatientProfileManager()
    profile = mgr.get_profile()

    assert profile.preferred_name == "Eleanor"
    assert profile.age == 76
    assert "Sarah Jenkins" in profile.primary_caregiver
    assert "Penicillin" in profile.known_allergies


def test_patient_profile_update():
    mgr = PatientProfileManager()
    mgr.update_profile(preferred_name="Nora", age=77)
    profile = mgr.get_profile()

    assert profile.preferred_name == "Nora"
    assert profile.age == 77
