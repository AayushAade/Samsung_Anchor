"""
Samsung Anchor Cognitive Pipeline.

Executes one complete cognitive cycle.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import time

from src.cognition.memory_engine import MemoryEngine
from src.cognition.context_restoration_engine import ContextRestorationEngine
from src.cognition.context.registry import ContextProviderRegistry
from src.cognition.context.fusion_engine import ContextFusionEngine
from src.cognition.context.providers.identity import IdentityContextProvider
from src.cognition.context.providers.memory import MemoryContextProvider
from src.cognition.context.providers.temporal import TemporalContextProvider
from src.cognition.context.providers.continuity import ContinuityContextProvider
from src.cognition.context.providers.social import SocialContextProvider
from src.cognition.context.providers.assistance import AssistanceContextProvider
from src.cognition.goals.inference_engine import GoalInferenceEngine
from src.conversation.conversation_manager import ConversationManager

from src.clinical.patient_profile import PatientProfileManager
from src.clinical.caregiver_manager import CaregiverManager
from src.clinical.medication_manager import MedicationManager
from src.clinical.appointment_manager import AppointmentManager
from src.clinical.consent_manager import ConsentManager
from src.clinical.audit_logger import AuditLogger
from src.clinical.explainability import ExplainabilityEngine
from src.clinical.emergency_manager import EmergencyManager

from src.perception.perception_manager import PerceptionManager

from src.runtime.runtime_manager import RuntimeManager

from deployment.configs.config_manager import ConfigManager
from deployment.health.health_checker import HealthChecker
from deployment.metrics.metrics_collector import MetricsCollector
from deployment.logging.structured_logger import StructuredLogger

from src.interaction.actions import InteractionAction
from src.interaction.interaction_manager import InteractionManager
from src.core.metrics import metrics
from src.core.cognitive_stream import CognitiveStream
import traceback
from src.interaction.presence_engine import PresenceEngine

if TYPE_CHECKING:
    from src.memory.database import MemoraDatabase

class CognitivePipeline:

    def __init__(self, database: "MemoraDatabase") -> None:
        
        self.database = database
        self.presence_engine = PresenceEngine()

        # Inject the real SQLAlchemy-backed memory repository
        self.memory_repository = self.database.memory_repo

        self.memory_engine = MemoryEngine(
            self.memory_repository
        )
        
        # Setup Context Framework
        self.context_registry = ContextProviderRegistry()
        self.context_registry.register(IdentityContextProvider())
        self.context_registry.register(MemoryContextProvider(self.memory_engine))
        self.context_registry.register(TemporalContextProvider())
        self.context_registry.register(ContinuityContextProvider())
        self.context_registry.register(SocialContextProvider())
        self.context_registry.register(AssistanceContextProvider())
        
        self.context_fusion_engine = ContextFusionEngine(self.context_registry)

        self.goal_inference_engine = GoalInferenceEngine()

        self.context_restoration_engine = ContextRestorationEngine()

        self.interaction_manager = InteractionManager()

        self.conversation_manager = ConversationManager()

        # Setup Clinical Ecosystem Layer
        self.patient_profile_mgr = PatientProfileManager()
        self.caregiver_mgr = CaregiverManager()
        self.medication_mgr = MedicationManager()
        self.appointment_mgr = AppointmentManager()
        self.consent_mgr = ConsentManager()
        self.audit_logger = AuditLogger()
        self.explainability_engine = ExplainabilityEngine()
        self.emergency_mgr = EmergencyManager()

        # Setup Edge Perception Layer
        self.perception_manager = PerceptionManager()

        # Setup Hardware Runtime Layer
        self.runtime_manager = RuntimeManager()

        # Setup Deployment & Operations Platform
        self.config_mgr = ConfigManager()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self.logger = StructuredLogger()

    def reset(self):
        self.presence_engine.reset()
        self.conversation_manager.reset()

    def process(
        self,
        recognition_result: dict,
    ) -> list[InteractionAction]:

        actions = []
        stream = CognitiveStream.instance()
        cycle_id = stream.next_cycle_id()
        cycle_start = time.perf_counter()
        
        try:
            metrics.start_timer("latency.cognition.total")
            
            # --------------------------------------------------
            # 0. Real-Time Edge Perception Cycle
            # --------------------------------------------------
            perception_context = self.perception_manager.process_cycle(recognition_result)

            # --------------------------------------------------
            # 1. Evaluate Presence
            # --------------------------------------------------
            
            event = self.presence_engine.process(recognition_result)
            
            if event is None:
                metrics.stop_timer("latency.cognition.total")
                return actions
                
            # --------------------------------------------------
            # 2. Collect Multimodal Context
            # --------------------------------------------------
            metrics.start_timer("latency.context.fusion")
            cognitive_context = self.context_fusion_engine.fuse_context(event)
            metrics.stop_timer("latency.context.fusion")
            
            # Optional Debugging output:
            mem_count = len(cognitive_context.memory.memories) if cognitive_context.memory else 0
            print(f"[DEBUG] Context Gathered. Memories: {mem_count}, Time: {cognitive_context.temporal.time_of_day if cognitive_context.temporal else 'Unknown'}")
            
            # --------------------------------------------------
            # 3. Goal Inference
            # --------------------------------------------------
            metrics.start_timer("latency.cognition.goal_inference")
            goal_hypotheses = self.goal_inference_engine.infer(cognitive_context)
            metrics.stop_timer("latency.cognition.goal_inference")
            
            # --------------------------------------------------
            # 4. Context Restoration & Attention
            # --------------------------------------------------
            metrics.start_timer("latency.cognition.attention_and_llm")
            recall = self.context_restoration_engine.generate_context_cue(
                cognitive_context=cognitive_context,
                goal_hypotheses=goal_hypotheses
            )
            metrics.stop_timer("latency.cognition.attention_and_llm")
            
            # --------------------------------------------------
            # 5. Conversation Behavior Engine
            # --------------------------------------------------
            attention_decision = self.context_restoration_engine.attention_engine.evaluate(cognitive_context) if cognitive_context else None
            should_interrupt = attention_decision.should_interrupt if attention_decision else False
            conversation_context = self.conversation_manager.process_cycle(
                event=event,
                cognitive_context=cognitive_context,
                attention_should_interrupt=should_interrupt
            )

            # --------------------------------------------------
            # 6. Interaction Manager
            # --------------------------------------------------
            action = self.interaction_manager.handle_event(
                event,
                recall,
            )
            
            if action is not None:
                actions.append(action)
                
            total_latency = time.perf_counter() - cycle_start
            metrics.stop_timer("latency.cognition.total")
            
            # --------------------------------------------------
            # 7. Clinical Ecosystem & Audit Logging
            # --------------------------------------------------
            ast_lvl = getattr(cognitive_context.assistance, "level_code", 0) if cognitive_context and cognitive_context.assistance else 0
            strat_val = getattr(getattr(conversation_context, "response_strategy", None), "value", "Supportive Silence")
            pres_state = "PERMITTED" if (attention_decision and attention_decision.should_interrupt) or event.name else "SUPPRESSED"

            explanation = self.explainability_engine.explain_decision(
                presence_allowed=(pres_state == "PERMITTED"),
                assistance_level=ast_lvl,
                strategy=strat_val,
                reason="Routine memory cue requested"
            )

            self.audit_logger.log_intervention(
                reason="Cognitive cycle evaluation",
                module="CognitivePipeline",
                decision=actions[0].message if actions else "Silent Observation",
                assistance_level=ast_lvl,
                presence_state=pres_state,
                strategy=strat_val,
                outcome="DELIVERED"
            )

            from src.clinical.clinical_models import ConsentFeature
            clinical_context = {
                "patient_name": self.patient_profile_mgr.get_profile().preferred_name,
                "primary_caregiver": self.patient_profile_mgr.get_profile().primary_caregiver,
                "pending_medications": [m.medication_name for m in self.medication_mgr.get_missed_medications()],
                "upcoming_appointments": [a.title for a in self.appointment_mgr.get_upcoming_appointments()],
                "consent_granted": self.consent_mgr.is_consent_granted(ConsentFeature.VOICE_RECORDING),
                "emergency_active": self.emergency_mgr.get_current_state().active,
                "explanation_reason": explanation.reason,
            }

            runtime_summary = self.runtime_manager.get_runtime_summary()

            self.metrics_collector.record_cycle(total_latency)
            self.logger.info("Cognitive cycle complete", cycle_id=cycle_id, latency_ms=total_latency)

            ops_summary = {
                "deployment_profile": self.config_mgr.get_profile().value,
                "system_health": self.health_checker.check_health()["overall_status"],
                "total_cycles": self.metrics_collector.total_cycles,
                "active_errors": self.metrics_collector.errors_count,
            }

            # --------------------------------------------------
            # 8. Emit to Experience Platform
            # --------------------------------------------------
            try:
                stream_event = CognitiveStream.build_event(
                    cycle_id=cycle_id,
                    cognitive_context=cognitive_context,
                    attention_decision=attention_decision,
                    goal_hypotheses=goal_hypotheses,
                    generated_response=recall.generated_response if recall else "",
                    final_action=actions[0].message if actions else "",
                    total_latency_ms=total_latency,
                    conversation_context=conversation_context,
                    clinical_context=clinical_context,
                    perception_context=perception_context,
                    runtime_summary=runtime_summary,
                    ops_summary=ops_summary,
                )
                stream.emit(stream_event)
            except Exception:
                pass  # Never let stream emission crash the pipeline
            
        except Exception as e:
            print(f"[CognitivePipeline] FATAL ERROR: {e}")
            traceback.print_exc()
            # Graceful degradation: If anything fails, don't crash the background thread.
            # We can optionally issue a generic error interaction or just fail silently.
            pass

        return actions