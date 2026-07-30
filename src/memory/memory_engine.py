"""
MEMORA Central Memory Engine.

Orchestrates MemoryRepository, MemoryEncoder, MemoryConsolidator, MemoryIndex, MemoryRecallEngine,
ContextReconstructor, AssociativeMemoryEngine, RetentionManager, ForgettingManager, MemoryValidator, and MemoryExplainer.

Positioned as the exclusive long-term cognitive memory subsystem. Inherits from ICognitiveSubsystem.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.memory.memory_models import MemoryCategory, MemoryRecord, RetentionPolicy
from src.memory.memory_repository import MemoryRepository
from src.memory.memory_encoder import MemoryEncoder
from src.memory.memory_consolidator import MemoryConsolidator
from src.memory.memory_index import MemoryIndex
from src.memory.memory_recall_engine import MemoryRecallEngine
from src.memory.context_reconstructor import ContextReconstructor
from src.memory.associative_memory import AssociativeMemoryEngine
from src.memory.retention_manager import RetentionManager
from src.memory.forgetting_manager import ForgettingManager
from src.memory.memory_validator import MemoryValidator
from src.memory.memory_explainer import MemoryExplainer


class MemoryEngine(ICognitiveSubsystem):
    """
    Central Long-Term Memory Subsystem Orchestrator.
    """

    def __init__(self, repository: Optional[Any] = None) -> None:
        self.repository = repository if isinstance(repository, MemoryRepository) else MemoryRepository()
        self.consolidator = MemoryConsolidator(self.repository)
        self.index = MemoryIndex(self.repository)
        self.recall_engine = MemoryRecallEngine(self.repository, self.index)
        self.context_reconstructor = ContextReconstructor(self.repository)
        self.associative_engine = AssociativeMemoryEngine()
        self.forgetting_manager = ForgettingManager(self.repository)
        self._cycle_counter = 0
        self._status = "INITIALIZED"
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        with self._lock:
            self._status = "RUNNING"
            return True

    def shutdown(self) -> bool:
        with self._lock:
            self._status = "SHUTDOWN"
            return True

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_cycle(
            user_speech=input_data.get("user_speech"),
            location=input_data.get("location", "Living Room"),
        )

    def status(self) -> str:
        with self._lock:
            return self._status

    def health(self) -> Dict[str, Any]:
        with self._lock:
            val = MemoryValidator.validate_repository(self.repository)
            return {
                "status": self._status,
                "is_repository_valid": val["is_valid"],
                "active_memories": val["active_count"],
                "archived_memories": val["archived_count"],
            }

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {"cycle_count": self._cycle_counter}

    def explain(self) -> str:
        recalled, exp = self.recall_engine.recall_by_keyword("Glasses")
        if recalled:
            return f"Memory Subsystem: Recalled '{recalled[0].content}'."
        return "Memory Subsystem: Operational with baseline cognitive memories."

    def process_cycle(
        self,
        user_speech: Optional[str] = None,
        location: str = "Living Room",
    ) -> Dict[str, Any]:
        """
        Execute one cycle of memory consolidation, recall, and retention evaluation.
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        # 1. Encode user speech as observation if present
        if user_speech:
            new_rec = MemoryEncoder.encode_observation(
                content=f"User stated: '{user_speech}'",
                context_snapshot={"location": location},
            )
            self.consolidator.consolidate_new_record(new_rec)

        # 2. Perform deterministic memory recall for active context
        recalled, exp_narrative = self.recall_engine.recall_by_keyword(location)

        # 3. Reconstruct context for top recalled memory
        reconstructed = None
        if recalled:
            reconstructed = self.context_reconstructor.reconstruct_context(recalled[0]).to_dict()

        # 4. Evaluate retention & archive expired memories
        self.forgetting_manager.evaluate_and_archive_expired()

        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        return {
            "cycle": self._cycle_counter,
            "active_memories_count": len(self.repository.get_all_active()),
            "archived_memories_count": len(self.repository.get_all_archived()),
            "recalled_memories": [m.to_dict() for m in recalled],
            "reconstructed_context": reconstructed,
            "explanation_narrative": exp_narrative,
            "memory_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self._cycle_counter = 0
            self.repository.clear()
            self.repository._seed_baseline_memories()
