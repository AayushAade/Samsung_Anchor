"""
MEMORA Entity Registry.

Provides thread-safe registration, lookup, and query indexing for deterministic world entities across 11 types:
PERSON, CAREGIVER, PATIENT, MEDICATION, OBJECT, ROOM, LOCATION, ROUTINE, REMINDER, APPOINTMENT, DEVICE
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.knowledge.knowledge_models import Entity, EntityType


class EntityRegistry:
    """
    Thread-safe registry for world entities.
    """

    def __init__(self) -> None:
        self._entities: Dict[str, Entity] = {}
        self._name_index: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._seed_baseline_entities()

    def register_entity(self, entity: Entity) -> Entity:
        with self._lock:
            self._entities[entity.entity_id] = entity
            self._name_index[entity.name.lower()] = entity.entity_id
            return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        with self._lock:
            return self._entities.get(entity_id)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        with self._lock:
            eid = self._name_index.get(name.lower())
            return self._entities.get(eid) if eid else None

    def query_by_type(self, entity_type: EntityType) -> List[Entity]:
        with self._lock:
            return [e for e in self._entities.values() if e.entity_type == entity_type]

    def get_all_entities(self) -> List[Entity]:
        with self._lock:
            return list(self._entities.values())

    def clear(self) -> None:
        with self._lock:
            self._entities.clear()
            self._name_index.clear()

    def _seed_baseline_entities(self) -> None:
        """Seed baseline world entities."""
        p_margaret = Entity(entity_id="ent-margaret", name="Margaret", entity_type=EntityType.PATIENT, attributes={"age": 78, "condition": "Mild Dementia"})
        c_sarah = Entity(entity_id="ent-sarah", name="Sarah", entity_type=EntityType.CAREGIVER, attributes={"relationship": "Daughter"})
        obj_glasses = Entity(entity_id="ent-glasses", name="Reading Glasses", entity_type=EntityType.OBJECT, attributes={"category": "Personal Items"})
        med_donepezil = Entity(entity_id="ent-donepezil", name="Donepezil Medication", entity_type=EntityType.MEDICATION, attributes={"dosage": "10mg", "frequency": "Daily Morning"})
        rm_living = Entity(entity_id="ent-living-room", name="Living Room", entity_type=EntityType.ROOM, attributes={"floor": 1})
        rm_bedroom = Entity(entity_id="ent-bedroom", name="Bedroom", entity_type=EntityType.ROOM, attributes={"floor": 1})
        rm_kitchen = Entity(entity_id="ent-kitchen", name="Kitchen", entity_type=EntityType.ROOM, attributes={"floor": 1})
        rm_dining = Entity(entity_id="ent-dining-room", name="Dining Room", entity_type=EntityType.ROOM, attributes={"floor": 1})

        for e in [p_margaret, c_sarah, obj_glasses, med_donepezil, rm_living, rm_bedroom, rm_kitchen, rm_dining]:
            self._entities[e.entity_id] = e
            self._name_index[e.name.lower()] = e.entity_id
