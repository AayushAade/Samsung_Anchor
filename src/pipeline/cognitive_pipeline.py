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
from src.clinical.patient_state import PatientStateEvaluator, PatientStateMode
from src.clinical.care_policy import CarePolicyFramework
from src.clinical.decision_trace import ClinicalDecisionTraceLogger
from src.perception.visual_memory_engine import VisualEpisodicMemoryEngine

from src.perception.perception_manager import PerceptionManager

from src.cognition.memory_encoder import MemoryEncoder
from src.runtime.runtime_models import HardwareConfig, SensorEvent, SensorEventType
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

    def __init__(
        self,
        database: "MemoraDatabase",
        config_mgr: Optional[ConfigManager] = None,
        hardware_config: Optional[HardwareConfig] = None,
    ) -> None:
        
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

        # Setup Deployment & Operations Platform
        self.config_mgr = config_mgr or ConfigManager()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self.logger = StructuredLogger()

        # Setup Hardware Runtime Layer with Explicit HardwareConfig Injection
        if hardware_config is None:
            active_mode = self.config_mgr.get_runtime_mode()
            hw_config = HardwareConfig(mode=active_mode)
        else:
            hw_config = hardware_config

        self.runtime_manager = RuntimeManager(config=hw_config)

        # Wire Edge Perception Layer to Hardware Runtime Layer
        self.perception_manager.camera_pipeline.set_camera_adapter(self.runtime_manager.camera)
        self.perception_manager.camera_pipeline.set_sensor_bus(self.runtime_manager.sensor_bus)
        self.perception_manager.audio_pipeline.set_microphone_adapter(self.runtime_manager.microphone)
        self.perception_manager.audio_pipeline.set_sensor_bus(self.runtime_manager.sensor_bus)

        # Closed-Loop Cognitive Wiring, Care Policy Framework & Visual Episodic Memory
        self.memory_encoder = MemoryEncoder(self.memory_repository)
        self.patient_state_evaluator = PatientStateEvaluator()
        self.care_policy_framework = CarePolicyFramework()
        self.clinical_trace_logger = ClinicalDecisionTraceLogger()
        self.visual_memory_engine = VisualEpisodicMemoryEngine(database)
        self._latest_transcript: Optional[str] = None
        self.runtime_manager.sensor_bus.subscribe(
            SensorEventType.SPEECH_TRANSCRIPT,
            self._on_speech_transcript,
        )

    def _on_speech_transcript(self, event: SensorEvent) -> None:
        if event and event.data and "text" in event.data:
            self._latest_transcript = event.data["text"]

    def reset(self):
        self.presence_engine.reset()
        self.conversation_manager.reset()
        self._latest_transcript = None

    def shutdown(self):
        """
        Gracefully shutdown hardware adapters and clear runtime resources.
        """
        self.runtime_manager.shutdown_hardware()

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
            
            # Inject latest SPEECH_TRANSCRIPT into recognition_result if present
            if self._latest_transcript:
                recognition_result["user_speech"] = self._latest_transcript
                self._latest_transcript = None

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
            # 6. Patient State & Care Policy Framework Evaluation
            # --------------------------------------------------
            action = self.interaction_manager.handle_event(
                event,
                recall,
            )
            
            u_speech = recognition_result.get("user_speech") or self._latest_transcript
            missed_meds = [m.medication_name for m in self.medication_mgr.get_missed_medications()]
            is_emerg = self.emergency_mgr.get_current_state().active

            self.current_patient_state = self.patient_state_evaluator.evaluate(
                cognitive_context=cognitive_context,
                presence_event=event,
                user_speech=u_speech,
                emergency_active=is_emerg,
                missed_medications=missed_meds,
            )

            p_profile = self.patient_profile_mgr.get_profile()

            # --------------------------------------------------
            # 6.1 Visual Episodic Memory Location Retrieval
            # --------------------------------------------------
            if u_speech and any(w in u_speech.lower() for w in ["where", "glasses", "cane", "keys", "remote", "bottle"]):
                v_res = self.visual_memory_engine.recall_object_location(u_speech, p_profile.preferred_name)
                if v_res.get("found") and v_res.get("response"):
                    from src.interaction.actions import InteractionAction, InteractionActionType
                    action = InteractionAction(type=InteractionActionType.SPEAK, message=v_res["response"])

            care_decision = self.care_policy_framework.evaluate_policy(
                patient_state=self.current_patient_state,
                current_message=action.message if action else None,
                patient_name=p_profile.preferred_name,
                location=getattr(event, "room", "Living Room"),
            )

            if action is not None:
                if care_decision.message_override:
                    from src.interaction.actions import InteractionAction
                    action = InteractionAction(type=action.type, message=care_decision.message_override)

                if care_decision.action_type != "SILENCE":
                    actions.append(action)
                    # Physical Audio Output via Speaker HAL
                    if hasattr(action, "message") and action.message:
                        self.runtime_manager.speaker.speak(action.message)

                # Automatic Experience Encoding into MemoryRepository
                p_name = getattr(event, "name", p_profile.preferred_name) or p_profile.preferred_name
                p_room = getattr(event, "room", "Living Room")
                loc_val = p_room.value if hasattr(p_room, "value") else str(p_room)
                c_time = cognitive_context.temporal.time_of_day if cognitive_context and cognitive_context.temporal else "Day"
                self.memory_encoder.encode_experience(
                    person_name=p_name,
                    location=loc_val,
                    content=action.message,
                    context=f"State: {self.current_patient_state.mode.value}, Time: {c_time}",
                )
                
            total_latency = time.perf_counter() - cycle_start
            metrics.stop_timer("latency.cognition.total")

            # --------------------------------------------------
            # 7. Clinical Decision Trace & Audit Logging
            # --------------------------------------------------
            speech_produced = bool(action and hasattr(action, "message") and action.message and care_decision.action_type != "SILENCE")
            memory_written = bool(action is not None)
            strat_name = getattr(getattr(conversation_context, "response_strategy", None), "value", "Supportive Silence")

            self.latest_clinical_trace = self.clinical_trace_logger.record_trace(
                patient_state=self.current_patient_state,
                cognitive_context=cognitive_context,
                goal_hypotheses=goal_hypotheses,
                care_decision=care_decision,
                interaction_strategy=strat_name,
                speech_produced=speech_produced,
                memory_written=memory_written,
                final_response=action.message if (action and speech_produced) else "Supportive Silence",
            )
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