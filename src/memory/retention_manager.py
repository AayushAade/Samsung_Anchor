"""
MEMORA Retention Manager.

Evaluates deterministic memory retention rules:
- CLINICAL: Never expires
- TEMPORARY: 30 days retention
- DIAGNOSTIC: 7 days retention
"""

from __future__ import annotations

import time
from typing import Dict, List

from src.memory.memory_models import MemoryRecord, RetentionPolicy


class RetentionManager:
    """
    Deterministic memory retention evaluator.
    """

    POLICY_EXPIRATION_SECONDS: Dict[RetentionPolicy, float] = {
        RetentionPolicy.CLINICAL: float("inf"),
        RetentionPolicy.TEMPORARY: 30 * 24 * 3600.0,
        RetentionPolicy.DIAGNOSTIC: 7 * 24 * 3600.0,
    }

    @classmethod
    def is_expired(cls, record: MemoryRecord, current_ts: float = 0.0) -> bool:
        if record.retention_policy == RetentionPolicy.CLINICAL:
            return False

        now = current_ts or time.time()
        max_age = cls.POLICY_EXPIRATION_SECONDS.get(record.retention_policy, 30 * 24 * 3600.0)
        age = now - record.created_ts
        return age > max_age
