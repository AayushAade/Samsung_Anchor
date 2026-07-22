from datetime import datetime
from typing import List
from src.clinical.clinical_models import AuditEntry


class AuditLogger:
    """
    Structured, privacy-first audit logging engine.
    Logs system interventions and clinical decisions without saving raw dialogue.
    """

    def __init__(self, max_entries: int = 100) -> None:
        self.max_entries = max_entries
        self._entries: List[AuditEntry] = []

    def log_intervention(
        self,
        reason: str,
        module: str,
        decision: str,
        assistance_level: int,
        presence_state: str,
        strategy: str,
        outcome: str = "DELIVERED",
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reason=reason,
            module=module,
            decision=decision,
            assistance_level=assistance_level,
            presence_state=presence_state,
            strategy=strategy,
            outcome=outcome,
        )
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)
        return entry

    def get_recent_entries(self, limit: int = 10) -> List[AuditEntry]:
        return self._entries[-limit:]
