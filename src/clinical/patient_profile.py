from typing import Optional
from src.clinical.clinical_models import PatientProfile


class PatientProfileManager:
    """
    Manages structured patient clinical demographics and preferences.
    """

    def __init__(self, profile: Optional[PatientProfile] = None) -> None:
        self._profile = profile or PatientProfile()

    def get_profile(self) -> PatientProfile:
        return self._profile

    def update_profile(self, **kwargs) -> PatientProfile:
        for key, value in kwargs.items():
            if hasattr(self._profile, key):
                setattr(self._profile, key, value)
        return self._profile

    def get_summary(self) -> str:
        p = self._profile
        return f"Patient: {p.preferred_name}, Age: {p.age}, Diagnosis: {p.primary_diagnosis} ({p.stage})"
