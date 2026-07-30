"""
MEMORA Memory Explainer.

Generates caregiver-readable narrative explanations for memory recall operations and consolidation choices.
"""

from __future__ import annotations

from typing import List

from src.memory.memory_models import MemoryRecord, ReconstructedContext


class MemoryExplainer:
    """
    Generates human-readable explanations of memory recall and consolidation decisions.
    """

    @classmethod
    def generate_recall_explanation(
        cls, query_type: str, recalled_memories: List[MemoryRecord], explanation_text: str
    ) -> str:
        lines = [
            f"### Long-Term Memory Recall Explanation: '{query_type}'",
            f"- **Recalled Memories Count**: {len(recalled_memories)}",
            f"- **Recall Rationale**: {explanation_text}",
            "",
            "**Recalled Items**:",
        ]
        for m in recalled_memories:
            lines.append(
                f"  • `{m.memory_id}` [{m.category.value}] Importance: {m.importance:.2f} — \"{m.content}\""
            )

        return "\n".join(lines)
