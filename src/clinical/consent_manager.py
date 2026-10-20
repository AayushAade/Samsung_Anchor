from datetime import datetime
from typing import Any, Dict, Optional

from src.clinical.clinical_models import ConsentFeature, ConsentRecord

_KEY_PREFIX = "consent:"


class ConsentRequiredError(PermissionError):
    """Raised by storage layers when a write is attempted without the required consent."""


class ConsentManager:
    """
    Privacy-first consent enforcement engine.
    Ensures feature-level consent is explicitly granted before processing.

    Consent is never assumed: every feature starts as not granted. When a
    database is supplied, decisions persist across restarts (system_state keys
    "consent:<feature>" with value "granted|declined@<iso timestamp>"), and
    `has_decided` distinguishes "never asked" from "declined".
    """

    def __init__(self, database: Optional[Any] = None) -> None:
        self.db = database
        self._decided: Dict[ConsentFeature, Optional[str]] = {feature: None for feature in ConsentFeature}
        self._consents: Dict[ConsentFeature, ConsentRecord] = {
            feature: ConsentRecord(feature=feature, granted=False)
            for feature in ConsentFeature
        }
        if self.db is not None and hasattr(self.db, "_get_system_state"):
            for feature in ConsentFeature:
                raw = self.db._get_system_state(_KEY_PREFIX + feature.name)
                if raw:
                    decision, _, when = raw.partition("@")
                    self._consents[feature].granted = decision == "granted"
                    self._decided[feature] = when or "unknown time"

    def is_consent_granted(self, feature: ConsentFeature) -> bool:
        rec = self._consents.get(feature)
        return rec.granted if rec else False

    def has_decided(self, feature: ConsentFeature) -> bool:
        return self._decided.get(feature) is not None

    def update_consent(self, feature: ConsentFeature, granted: bool) -> ConsentRecord:
        rec = self._consents.get(feature)
        if rec:
            rec.granted = granted
        else:
            rec = ConsentRecord(feature=feature, granted=granted)
            self._consents[feature] = rec
        when = datetime.now().isoformat(timespec="seconds")
        self._decided[feature] = when
        if self.db is not None and hasattr(self.db, "_set_system_state"):
            self.db._set_system_state(_KEY_PREFIX + feature.name, f"{'granted' if granted else 'declined'}@{when}")
        return rec

    def get_consent_summary(self) -> Dict[str, bool]:
        return {f.value: r.granted for f, r in self._consents.items()}
