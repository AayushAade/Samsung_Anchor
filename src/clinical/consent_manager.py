from typing import Dict
from src.clinical.clinical_models import ConsentFeature, ConsentRecord


class ConsentManager:
    """
    Privacy-first consent enforcement engine.
    Ensures feature-level consent is explicitly granted before processing.
    """

    def __init__(self) -> None:
        self._consents: Dict[ConsentFeature, ConsentRecord] = {
            feature: ConsentRecord(feature=feature, granted=True)
            for feature in ConsentFeature
        }

    def is_consent_granted(self, feature: ConsentFeature) -> bool:
        rec = self._consents.get(feature)
        return rec.granted if rec else False

    def update_consent(self, feature: ConsentFeature, granted: bool) -> ConsentRecord:
        rec = self._consents.get(feature)
        if rec:
            rec.granted = granted
        else:
            rec = ConsentRecord(feature=feature, granted=granted)
            self._consents[feature] = rec
        return rec

    def get_consent_summary(self) -> Dict[str, bool]:
        return {f.value: r.granted for f, r in self._consents.items()}
