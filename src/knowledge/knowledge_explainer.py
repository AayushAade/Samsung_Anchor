"""
MEMORA Knowledge Explainer.

Generates human-readable explanations for graph query results and graph traversals.
"""

from __future__ import annotations

from typing import List

from src.knowledge.knowledge_models import Entity


class KnowledgeExplainer:
    """
    Generates human-readable explanations of knowledge graph query results.
    """

    @classmethod
    def generate_query_explanation(cls, query_type: str, results: List[Entity], explanation_steps: List[str]) -> str:
        lines = [
            f"### Knowledge Graph Query Explanation: '{query_type}'",
            f"- **Found Entities**: {len(results)}",
            "",
            "**Deterministic Traversal Steps**:",
        ]
        for step in explanation_steps:
            lines.append(f"  • {step}")

        return "\n".join(lines)
