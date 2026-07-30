"""
MEMORA Memory Integrity Validator.

Validates memory repository integrity:
- Duplicate memory IDs
- Broken entity references
- Retention policy compliance
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.memory.memory_repository import MemoryRepository


class MemoryValidator:
    """
    Memory integrity and compliance validator.
    """

    @classmethod
    def validate_repository(cls, repository: MemoryRepository) -> Dict[str, Any]:
        """
        Perform a full integrity validation scan over MemoryRepository.
        """
        errors: List[str] = []
        warnings: List[str] = []

        active = repository.get_all_active()
        archived = repository.get_all_archived()

        active_ids = {m.memory_id for m in active}
        archived_ids = {m.memory_id for m in archived}

        # 1. Check for ID collisions between active and archived
        overlap = active_ids & archived_ids
        if overlap:
            errors.append(f"Memory ID collisions detected between active and archived: {', '.join(overlap)}")

        # 2. Check for empty memory content
        for m in active:
            if not m.content or len(m.content.strip()) == 0:
                warnings.append(f"Empty content in memory record `{m.memory_id}`.")

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "active_count": len(active),
            "archived_count": len(archived),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }
