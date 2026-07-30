"""
MEMORA Knowledge Graph.

Coordinates entities, relationships, facts, and contexts into a unified, thread-safe graph network.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.knowledge.entity_registry import EntityRegistry
from src.knowledge.relationship_registry import RelationshipRegistry
from src.knowledge.knowledge_models import Entity, Relationship, RelationshipType


class KnowledgeGraph:
    """
    Unified Knowledge Graph network model.
    """

    def __init__(
        self,
        entity_registry: Optional[EntityRegistry] = None,
        relationship_registry: Optional[RelationshipRegistry] = None,
    ) -> None:
        self.entities = entity_registry or EntityRegistry()
        self.relationships = relationship_registry or RelationshipRegistry()

    def add_entity(self, entity: Entity) -> Entity:
        return self.entities.register_entity(entity)

    def add_relationship(self, relationship: Relationship) -> Relationship:
        return self.relationships.register_relationship(relationship)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get_entity(entity_id)

    def get_neighbors(
        self, entity_id: str, relationship_type: Optional[RelationshipType] = None
    ) -> List[Tuple[Entity, Relationship]]:
        """
        Get all outgoing neighbor entities and their connecting relationships.
        """
        results: List[Tuple[Entity, Relationship]] = []
        rels = self.relationships.get_outgoing_relationships(entity_id)
        for r in rels:
            if relationship_type and r.relationship_type != relationship_type:
                continue
            tgt = self.entities.get_entity(r.target_entity_id)
            if tgt:
                results.append((tgt, r))
        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities_count": len(self.entities.get_all_entities()),
            "relationships_count": len(self.relationships.get_all_relationships()),
            "entities": [e.to_dict() for e in self.entities.get_all_entities()],
            "relationships": [r.to_dict() for r in self.relationships.get_all_relationships()],
        }
