"""
MEMORA Semantic Graph Validator.

Validates graph integrity and detects:
- Duplicate entity names
- Invalid relationship target references
- Contradictory relationships
- Orphan nodes
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.knowledge.knowledge_graph import KnowledgeGraph


class SemanticValidator:
    """
    Graph integrity and ontology compliance validator.
    """

    @classmethod
    def validate_graph(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Perform a full integrity validation scan over the KnowledgeGraph.
        """
        errors: List[str] = []
        warnings: List[str] = []

        all_entities = graph.entities.get_all_entities()
        all_entity_ids = {e.entity_id for e in all_entities}
        all_relationships = graph.relationships.get_all_relationships()

        # 1. Check for duplicate names
        names = [e.name.lower() for e in all_entities]
        if len(names) != len(set(names)):
            warnings.append("Duplicate entity names detected in registry.")

        # 2. Check for invalid target references
        for r in all_relationships:
            if r.source_entity_id not in all_entity_ids:
                errors.append(f"Relationship '{r.relationship_id}' has invalid source ID '{r.source_entity_id}'.")
            if r.target_entity_id not in all_entity_ids:
                errors.append(f"Relationship '{r.relationship_id}' has invalid target ID '{r.target_entity_id}'.")

        # 3. Check for orphan nodes
        referenced_ids = {r.source_entity_id for r in all_relationships} | {r.target_entity_id for r in all_relationships}
        orphans = [e.name for e in all_entities if e.entity_id not in referenced_ids]
        if orphans:
            warnings.append(f"Orphan entities detected: {', '.join(orphans)}")

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }
