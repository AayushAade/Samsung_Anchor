"""
Persistence for care items (medication schedules, appointments) and care events.

Everything here is entered by the person or a caregiver; MEMORA never invents
schedules. A dose is only ever *reported* taken (from what the person says),
never verified.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Callable, Optional

from src.clinical.consent_manager import ConsentRequiredError

from src.memory.models import CareEventModel, CareItemModel

REPORTED_TAKEN = "REPORTED_TAKEN"
REMINDED = "REMINDED"


class CareStore:
    def __init__(self, database: Any, storage_allowed: Optional[Callable[[], bool]] = None) -> None:
        self.db = database
        # Set by the pipeline: care records are personal data stored only with consent.
        self.storage_allowed = storage_allowed

    def _require_consent(self) -> None:
        if self.storage_allowed is not None and not self.storage_allowed():
            raise ConsentRequiredError("Saving care records requires storage consent.")

    def add_item(self, kind: str, title: str, scheduled_time: Optional[str], detail: str = "",
                 entered_by: str = "user (chat)") -> str:
        self._require_consent()
        item_id = f"{kind[:3]}_{uuid.uuid4().hex[:12]}"
        with self.db._session_scope() as s:
            s.add(CareItemModel(item_id=item_id, kind=kind, title=title, detail=detail,
                                scheduled_time=scheduled_time, entered_by=entered_by,
                                created_at=datetime.now().isoformat(), active=1))
        return item_id

    def items(self, kind: str) -> list[CareItemModel]:
        with self.db.SessionFactory() as s:
            rows = (s.query(CareItemModel).filter_by(kind=kind, active=1)
                    .order_by(CareItemModel.scheduled_time, CareItemModel.created_at).all())
            s.expunge_all()
            return rows

    def remove_item(self, item_id: str) -> bool:
        with self.db._session_scope() as s:
            s.query(CareEventModel).filter_by(item_id=item_id).delete()
            return bool(s.query(CareItemModel).filter_by(item_id=item_id).delete())

    def record_event(self, item_id: str, event_type: str, source: str, when: Optional[datetime] = None) -> None:
        self._require_consent()
        with self.db._session_scope() as s:
            s.add(CareEventModel(item_id=item_id, event_type=event_type, source=source,
                                 timestamp=(when or datetime.now()).isoformat()))

    def last_event(self, item_id: str, event_type: str, on: Optional[date] = None) -> Optional[datetime]:
        with self.db.SessionFactory() as s:
            q = s.query(CareEventModel).filter_by(item_id=item_id, event_type=event_type)
            if on is not None:
                q = q.filter(CareEventModel.timestamp.startswith(on.isoformat()))
            row = q.order_by(CareEventModel.timestamp.desc()).first()
            return datetime.fromisoformat(row.timestamp) if row else None
