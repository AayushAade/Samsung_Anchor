"""
MEMORA Knowledge Query Engine.

Provides deterministic, non-probabilistic graph queries over KnowledgeGraph:
- Find medications for patient
- Find objects located in room
- Find connected rooms
- Find routines involving caregiver
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.knowledge.knowledge_graph import KnowledgeGraph
from src.knowledge.knowledge_models import Entity, EntityType, RelationshipType


class KnowledgeQueryEngine:
    """
    Deterministic graph query engine.
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def find_medications_for_patient(self, patient_name_or_id: str) -> List[Entity]:
        """
        Find all medications that belong to a specific patient.
        """
        patient = self.graph.entities.get_entity_by_name(patient_name_or_id) or self.graph.entities.get_entity(patient_name_or_id)
        if not patient:
            return []

        meds: List[Entity] = []
        all_meds = self.graph.entities.query_by_type(EntityType.MEDICATION)
        for med in all_meds:
            rels = self.graph.relationships.get_outgoing_relationships(med.entity_id)
            if any(r.target_entity_id == patient.entity_id and r.relationship_type == RelationshipType.BELONGS_TO for r in rels):
                meds.append(med)
        return meds

    def find_objects_in_room(self, room_name_or_id: str) -> List[Entity]:
        """
        Find all objects located in a specific room.
        """
        room = self.graph.entities.get_entity_by_name(room_name_or_id) or self.graph.entities.get_entity(room_name_or_id)
        if not room:
            return []

        objects: List[Entity] = []
        all_objs = self.graph.entities.query_by_type(EntityType.OBJECT)
        for obj in all_objs:
            rels = self.graph.relationships.get_outgoing_relationships(obj.entity_id)
            if any(r.target_entity_id == room.entity_id and r.relationship_type == RelationshipType.LOCATED_IN for r in rels):
                objects.append(obj)
        return objects

    def find_connected_rooms(self, room_name_or_id: str) -> List[Entity]:
        """
        Find all rooms connected to a given room.
        """
        room = self.graph.entities.get_entity_by_name(room_name_or_id) or self.graph.entities.get_entity(room_name_or_id)
        if not room:
            return []

        neighbors = self.graph.get_neighbors(room.entity_id, relationship_type=RelationshipType.CONNECTED_TO)
        return [ent for ent, rel in neighbors if ent.entity_type == EntityType.ROOM]
