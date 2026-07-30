"""
MEMORA Session Context.

A lightweight reference container connecting existing subsystem outputs for the
duration of one CognitiveSession. Holds references — never copies or owns data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionContext:
    """
    Shared reference context for one cognitive session.
    Stores references to subsystem outputs — never owns the underlying data.
    """

    runtime_metadata: Dict[str, Any] = field(default_factory=dict)
    working_memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    knowledge_references: List[str] = field(default_factory=list)
    memory_references: List[str] = field(default_factory=list)
    executive_goal: Optional[str] = None
    trust_decisions: List[str] = field(default_factory=list)
    reasoning_outcome: Optional[str] = None
    final_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_metadata": self.runtime_metadata,
            "working_memory_keys": list(self.working_memory_snapshot.keys()),
            "knowledge_references_count": len(self.knowledge_references),
            "memory_references_count": len(self.memory_references),
            "executive_goal": self.executive_goal,
            "trust_decisions_count": len(self.trust_decisions),
            "reasoning_outcome": self.reasoning_outcome,
            "final_response": self.final_response,
        }
