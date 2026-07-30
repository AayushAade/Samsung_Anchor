"""
MEMORA Graph Traverser.

Executes explainable, deterministic graph traversal algorithms:
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Shortest Path
- Neighborhood Expansion
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from src.knowledge.knowledge_graph import KnowledgeGraph
from src.knowledge.knowledge_models import Entity, Relationship


class GraphTraverser:
    """
    Explainable graph traversal engine over KnowledgeGraph.
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def find_shortest_path(
        self, start_entity_id: str, end_entity_id: str
    ) -> Tuple[List[Entity], List[str]]:
        """
        Find shortest path between two entities using BFS.
        Returns (list_of_entities, list_of_explanation_steps).
        """
        start = self.graph.get_entity(start_entity_id)
        end = self.graph.get_entity(end_entity_id)

        if not start or not end:
            return ([], ["Start or target entity does not exist in graph."])

        queue = deque([(start_entity_id, [start])])
        visited: Set[str] = {start_entity_id}
        steps: List[str] = [f"Starting BFS from entity '{start.name}' ({start.entity_id})."]

        while queue:
            curr_id, path = queue.popleft()
            if curr_id == end_entity_id:
                steps.append(f"Reached target entity '{end.name}' in {len(path)-1} hops.")
                return (path, steps)

            neighbors = self.graph.get_neighbors(curr_id)
            for neighbor_entity, rel in neighbors:
                nid = neighbor_entity.entity_id
                if nid not in visited:
                    visited.add(nid)
                    steps.append(f"Traversing via '{rel.relationship_type.value}' to '{neighbor_entity.name}'.")
                    queue.append((nid, path + [neighbor_entity]))

        return ([], [f"No graph path exists between '{start.name}' and '{end.name}'."])
