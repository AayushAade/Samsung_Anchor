"""
MEMORA Session Engine.

Thin orchestration wrapper around the existing CognitivePipeline.
Creates a CognitiveSession per interaction, delegates all work to the pipeline,
records subsystem participation and execution trace, then closes the session.

Does not replace, modify, or duplicate any pipeline logic.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.session.session_models import CognitiveSession, SessionState
from src.session.session_context import SessionContext
from src.session.session_manager import SessionManager
from src.session.session_explainer import SessionExplainer

if TYPE_CHECKING:
    from src.pipeline.cognitive_pipeline import CognitivePipeline


# Subsystems recorded per session cycle, in pipeline execution order.
_PIPELINE_SUBSYSTEMS = [
    "PerceptionManager",
    "PresenceEngine",
    "ContextFusionEngine",
    "GoalInferenceEngine",
    "CognitiveKernel",
    "MemoryEngine",
    "BehaviourManager",
    "CognitiveReasoningEngine",
    "KnowledgeEngine",
    "ExecutiveEngine",
    "ExperienceEngine",
    "SafetyManager",
    "CentralRuntimeEngine",
]


class SessionEngine:
    """
    Wraps CognitivePipeline execution inside CognitiveSession lifecycle.
    """

    def __init__(self) -> None:
        self.session_manager = SessionManager()
        self._latest_session: Optional[CognitiveSession] = None

    def execute(
        self,
        pipeline: "CognitivePipeline",
        recognition_result: Dict[str, Any],
        patient_id: str = "default-patient",
        goal: str = "",
    ) -> Dict[str, Any]:
        """
        Run one cognitive interaction inside a session.

        1. Create session
        2. Transition to RUNNING
        3. Invoke pipeline.process()
        4. Record subsystem participation and trace
        5. Transition to COMPLETED (or FAILED)
        6. Return session summary alongside pipeline actions
        """
        start = time.time()

        # 1. Create
        session = self.session_manager.create_session(
            patient_id=patient_id,
            goal=goal or f"Process input: {recognition_result.get('name', 'Unknown')}",
        )

        # 2. RUNNING
        self.session_manager.transition(session.session_id, SessionState.RUNNING, reason="Pipeline invoked")

        try:
            # 3. Delegate to existing pipeline
            actions = pipeline.process(recognition_result)

            # 4. Record participation
            for sub in _PIPELINE_SUBSYSTEMS:
                self.session_manager.record_subsystem(session.session_id, sub)

            elapsed_ms = round((time.time() - start) * 1000.0, 3)
            self.session_manager.record_trace_step(
                session.session_id,
                subsystem="CognitivePipeline",
                operation="process",
                duration_ms=elapsed_ms,
            )

            # 5. Complete
            final_result = {
                "action": actions[0].message if actions else "No action",
                "actions_count": len(actions),
                "latency_ms": elapsed_ms,
            }
            self.session_manager.complete_session(session.session_id, final_result)

        except Exception as e:
            self.session_manager.fail_session(session.session_id, str(e))

        self._latest_session = self.session_manager.get_session(session.session_id)
        return self._build_summary()

    def explain_latest(self) -> str:
        if self._latest_session:
            return SessionExplainer.explain(self._latest_session)
        return "No session has been executed yet."

    def _build_summary(self) -> Dict[str, Any]:
        if not self._latest_session:
            return {}
        return {
            "session": self._latest_session.to_dict(),
            "explanation": SessionExplainer.explain(self._latest_session),
        }
