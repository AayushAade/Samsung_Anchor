"""
Cognitive Operating System — Cognitive Event Graph.

Records causal chains of cognitive events within a session.
Enables reasoning traces, debugging, explainability, and future analytics.

In-memory only (resets per session). No external dependencies.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from src.cognition.cos.models import CognitiveGraphEvent


class CognitiveEventGraph:
    """
    Directed acyclic graph of cognitive events within a single session.

    Each event records a causal link (source → target) with optional
    parent linkage for chain traversal.
    """

    MAX_EVENTS = 500

    def __init__(self) -> None:
        self._events: list[CognitiveGraphEvent] = []
        self._lock = threading.Lock()

    def record_event(
        self,
        event_type: str,
        source: str,
        target: str,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Record a cognitive event in the graph.

        Parameters
        ----------
        event_type : str
            E.g., ``"VisitorRecognised"``, ``"MemoryRetrieved"``, ``"PolicySelected"``.
        source : str
            The subsystem that produced this event.
        target : str
            The subsystem or entity affected.
        parent_id : str | None
            The event ID of the causal predecessor (for chain linkage).
        metadata : dict | None
            Additional event payload.

        Returns
        -------
        str
            The generated event ID.
        """
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        event = CognitiveGraphEvent(
            event_id=event_id,
            event_type=event_type,
            source=source,
            target=target,
            timestamp=time.time(),
            parent_id=parent_id,
            metadata=metadata or {},
        )

        with self._lock:
            self._events.append(event)
            if len(self._events) > self.MAX_EVENTS:
                self._events = self._events[-self.MAX_EVENTS:]

        return event_id

    def get_chain(self, root_event_id: str) -> list[CognitiveGraphEvent]:
        """
        Traverse the causal chain starting from a root event.
        Returns events in chronological order.
        """
        with self._lock:
            chain: list[CognitiveGraphEvent] = []
            current_id = root_event_id

            # Build forward lookup: parent_id → children
            children_map: dict[str | None, list[CognitiveGraphEvent]] = {}
            for ev in self._events:
                children_map.setdefault(ev.parent_id, []).append(ev)

            # Find root
            root = next((e for e in self._events if e.event_id == root_event_id), None)
            if root:
                chain.append(root)

            # BFS forward traversal
            queue = [root_event_id]
            visited = {root_event_id}
            while queue:
                parent = queue.pop(0)
                for child in children_map.get(parent, []):
                    if child.event_id not in visited:
                        chain.append(child)
                        visited.add(child.event_id)
                        queue.append(child.event_id)

            return chain

    def get_session_graph(self) -> dict[str, Any]:
        """
        Return the full session event graph as a serialisable dictionary.
        """
        with self._lock:
            return {
                "event_count": len(self._events),
                "events": [e.to_dict() for e in self._events],
            }

    def get_recent_events(self, limit: int = 10) -> list[CognitiveGraphEvent]:
        """Return the most recent events."""
        with self._lock:
            return list(self._events[-limit:])

    def clear(self) -> None:
        """Reset the event graph."""
        with self._lock:
            self._events.clear()
