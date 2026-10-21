from src.clinical.clinical_models import ConsentFeature
from src.clinical.consent_manager import ConsentManager


def test_consent_manager_toggle():
    mgr = ConsentManager()
    # Consent must never be assumed.
    assert all(v is False for v in mgr.get_consent_summary().values())
    mgr.update_consent(ConsentFeature.VOICE_RECORDING, True)
    assert mgr.is_consent_granted(ConsentFeature.VOICE_RECORDING) is True

    mgr.update_consent(ConsentFeature.VOICE_RECORDING, False)
    assert mgr.is_consent_granted(ConsentFeature.VOICE_RECORDING) is False

    summary = mgr.get_consent_summary()
    assert summary[ConsentFeature.VOICE_RECORDING.value] is False
