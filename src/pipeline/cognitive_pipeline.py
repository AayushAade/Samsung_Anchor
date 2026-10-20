"""
Samsung Anchor Cognitive Pipeline.

Executes one complete cognitive cycle.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
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
from src.cognition.conversational_memory import ConversationalMemory
from src.cognition.cos.kernel import CognitiveKernel
from src.trust.safety_manager import SafetyManager
from src.trust.evidence_accumulator import EvidenceAccumulator
from src.trust.audit_framework import AuditFramework
from src.trust.caregiver_config import CaregiverConfigManager
from src.trust.privacy_manager import PrivacyManager
from src.trust.degradation_manager import DegradationManager
from src.behaviour.behaviour_manager import BehaviourManager
from src.reasoning.reasoning_engine import CognitiveReasoningEngine
from src.reasoning.intent_predictor import IntentPredictor
from src.executive.executive_engine import ExecutiveEngine
from src.experience.experience_engine import ExperienceEngine
from src.knowledge.knowledge_engine import KnowledgeEngine
from src.memory.memory_engine import MemoryEngine as LTMMemoryEngine
from src.runtime.runtime_engine import CentralRuntimeEngine
from src.session.session_engine import SessionEngine

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

import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.memory.database import MemoraDatabase

class CognitivePipeline:

    def __init__(
        self,
        database: "MemoraDatabase",
        config_mgr: Optional[ConfigManager] = None,
        hardware_config: Optional[HardwareConfig] = None,
        demo_data: bool = False,
    ) -> None:
        
        self.database = database
        # demo_data loads fictional medication schedules and object sightings for
        # scripted demonstrations. It must stay off for real use.
        self.demo_data = demo_data
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
        self.context_registry.register(ContinuityContextProvider(demo_data=demo_data))
        self.context_registry.register(SocialContextProvider())
        self.context_registry.register(AssistanceContextProvider(demo_data=demo_data))
        
        self.context_fusion_engine = ContextFusionEngine(self.context_registry)

        self.goal_inference_engine = GoalInferenceEngine()

        self.context_restoration_engine = ContextRestorationEngine()

        self.interaction_manager = InteractionManager()

        self.conversation_manager = ConversationManager()

        # Setup Clinical Ecosystem Layer
        self.patient_profile_mgr = PatientProfileManager()
        self.caregiver_mgr = CaregiverManager()
        # Person/caregiver-entered schedules persist in the user's database; demo
        # data is never written there.
        from src.clinical.care_store import CareStore
        from src.memory.database import MemoraDatabase as _MemoraDatabase
        care_store = CareStore(database) if (not demo_data and isinstance(database, _MemoraDatabase)) else None
        self.medication_mgr = MedicationManager(seed_demo_data=demo_data, store=care_store)
        self.appointment_mgr = AppointmentManager(seed_demo_data=demo_data, store=care_store)
        self.consent_mgr = ConsentManager()
        self.audit_logger = AuditLogger()
        self.explainability_engine = ExplainabilityEngine()
        self.emergency_mgr = EmergencyManager()

        # Setup Edge Perception Layer
        self.perception_manager = PerceptionManager(self.database)

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
        self.visual_memory_engine = VisualEpisodicMemoryEngine(database, seed_demo_data=demo_data)
        self.conversational_memory = ConversationalMemory(database, visual_memory=self.visual_memory_engine,
                                                          appointments=self.appointment_mgr,
                                                          medications=self.medication_mgr)
        self.cognitive_kernel = CognitiveKernel()
        
        # Phase 22 — Trust, Safety, Reliability & Data Lifecycle Infrastructure
        self.caregiver_config_mgr = CaregiverConfigManager()
        prefs = self.caregiver_config_mgr.get_preferences()
        self.safety_manager = SafetyManager(
            min_confidence_threshold=prefs.min_confidence_threshold,
            reminder_throttle_seconds=prefs.reminder_frequency_minutes * 60.0,
            quiet_hours_start=prefs.quiet_hours_start,
            quiet_hours_end=prefs.quiet_hours_end,
        )
        self.evidence_accumulator = EvidenceAccumulator()
        self.audit_framework = AuditFramework()
        self.privacy_manager = PrivacyManager()
        self.degradation_manager = DegradationManager()

        # Phase 23 — Behaviour Intelligence Platform Infrastructure
        self.behaviour_manager = BehaviourManager()

        # Phase 24 — Cognitive Reasoning Engine Framework
        self.reasoning_engine = CognitiveReasoningEngine()
        self.intent_predictor = IntentPredictor()

        # Phase 25 — Executive Function & Adaptive Planning Framework
        self.executive_engine = ExecutiveEngine()

        # Phase 26 — Experience Learning & Adaptive Knowledge Framework
        self.experience_engine = ExperienceEngine()

        # Phase 28 — Semantic Knowledge Graph & World Model
        self.knowledge_engine = KnowledgeEngine()

        # Phase 29 — Long-Term Memory Consolidation Framework
        self.ltm_memory_engine = LTMMemoryEngine()

        # Phase 30 — Clinical Runtime, Observability & Deployment Framework
        self.central_runtime = CentralRuntimeEngine()

        # Phase 31 — Cognitive Session Framework
        self.session_engine = SessionEngine()

        self._latest_transcript: Optional[str] = None
        # Scheduled reminders: per-dose throttle (caregiver-configurable interval).
        self._last_reminder_at: dict[str, float] = {}
        self.reminder_interval_s = max(60.0, prefs.reminder_frequency_minutes * 60.0)
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
        self.patient_state_evaluator.reset()
        self.emergency_mgr.clear_emergency()
        self._latest_transcript = None
        self.conversational_memory.search_history.clear()
        self._last_reminder_at.clear()

    def shutdown(self):
        """
        Gracefully shutdown hardware adapters and clear runtime resources.
        """
        self.runtime_manager.shutdown_hardware()

    def process(
        self,
        recognition_result: Optional[dict] = None,
        user_speech: Optional[str] = None,
        location: Optional[str] = None,
        return_dict: bool = False,
    ) -> Any:

        if recognition_result is None:
            recognition_result = {}
        if user_speech:
            recognition_result["user_speech"] = user_speech
        if location:
            recognition_result["location"] = location

        actions = []
        executive_summary = None
        self.last_speech_delivered = False
        self.last_cycle_error = None
        event = None
        stream = CognitiveStream.instance()
        cycle_id = stream.next_cycle_id()
        cycle_start = time.perf_counter()
        
        try:
            metrics.start_timer("latency.cognition.total")
            
            # Inject latest SPEECH_TRANSCRIPT into recognition_result if present
            if self._latest_transcript:
                recognition_result["user_speech"] = self._latest_transcript
                self._latest_transcript = None

            # Working Memory Reference Resolution (Anaphora)
            raw_u_speech = recognition_result.get("user_speech")
            if raw_u_speech:
                resolution = self.cognitive_kernel.working_memory.resolve_reference(raw_u_speech)
                if resolution.get("has_reference") and resolution.get("resolved_query"):
                    logger.debug(f"🗣️ [Working Memory Anaphora] Resolved '{raw_u_speech}' -> '{resolution['resolved_query']}' (Referent: {resolution.get('resolved_referent')})")
                    recognition_result["user_speech"] = resolution["resolved_query"]

            # --------------------------------------------------
            # 0. Real-Time Edge Perception Cycle
            # --------------------------------------------------
            perception_context = self.perception_manager.process_cycle(recognition_result)

            # --------------------------------------------------
            # 1. Evaluate Presence
            # --------------------------------------------------
            event = recognition_result.get("event")
            if event is None:
                event = self.presence_engine.process(recognition_result)

            if event is None and (recognition_result.get("user_speech") or self._latest_transcript):
                from src.interaction.events import PresenceEvent, PresenceEventType
                event = PresenceEvent(
                    type=PresenceEventType.PERSON_ARRIVED,
                    face_id="patient_self",
                    # The person's own name (never the fictional profile default outside demo).
                    name=self._patient_name() or None,
                    relationship="Self",
                )

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
            logger.debug(f"[DEBUG] Context Gathered. Memories: {mem_count}, Time: {cognitive_context.temporal.time_of_day if cognitive_context.temporal else 'Unknown'}")
            
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

            # Operational Phase 30 Clinical Runtime Cycle
            runtime_engine_summary = self.central_runtime.process_cycle()
            
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
            # 6.1 Contextual Memory Recall (direct answers to what was said)
            # --------------------------------------------------
            face_id = recognition_result.get("face_id")
            recall_msg = self._handle_contextual_recall(u_speech, event, p_profile, face_id=face_id)
            patient_name = self._patient_name()
            if u_speech:
                # The presence greeting is for people arriving on camera; it is not a
                # reply to something the person said.
                action = None
            elif action is None and self._is_known_visitor_arrival(event):
                # Attention gating only interrupts when stored memories score highly, which
                # meant a known visitor with no history was never announced. Announce
                # named visitors; unknown faces and the person themself stay silent.
                action = self.interaction_manager.handle_event(event, None)

            # --------------------------------------------------
            # 6.5 Cognitive Operating System & Safety Guardrails
            # --------------------------------------------------
            cos_action = self.cognitive_kernel.reason(
                context=cognitive_context,
                goals=goal_hypotheses,
                patient_state=self.current_patient_state,
                attention_decision=attention_decision,
            )

            # Mandatory Safety Guardrails Evaluation
            safety_eval = self.safety_manager.evaluate_action(
                action=cos_action,
                context=cognitive_context,
                goals=goal_hypotheses,
                patient_state=self.current_patient_state,
                working_memory_snapshot=self.cognitive_kernel.working_memory.snapshot(),
            )

            care_decision = self.care_policy_framework.evaluate_policy(
                patient_state=self.current_patient_state,
                current_message=recall_msg if u_speech else (action.message if action else None),
                patient_name=patient_name,
                location=getattr(event, "room", "Living Room"),
            )

            p_name = getattr(event, "name", None) or patient_name or "Patient"
            p_room = getattr(event, "room", "Living Room")
            loc_val = p_room.value if hasattr(p_room, "value") else str(p_room)
            c_time = cognitive_context.temporal.time_of_day if cognitive_context and cognitive_context.temporal else "Day"

            # Reply precedence (deterministic, independent of any language model):
            #   1. urgent-safety guidance
            #   2. a direct answer from conversational memory
            #   3. the care-policy reply to what the person said
            #   4. an honest fallback, so speech never goes unanswered
            #   5. without speech: presence-driven greeting, adjusted by care policy
            from src.clinical.care_policy import CarePrinciple
            from src.interaction.actions import InteractionAction, InteractionActionType

            def _speak(msg: str) -> InteractionAction:
                return InteractionAction(type=InteractionActionType.SPEAK, message=msg)

            if care_decision.principle == CarePrinciple.EMERGENCY_ESCALATION and care_decision.message_override:
                action = _speak(care_decision.message_override)
            elif recall_msg:
                action = _speak(recall_msg)
            elif u_speech and care_decision.action_type == "SPEAK" and care_decision.message_override:
                action = _speak(care_decision.message_override)
            elif u_speech:
                action = _speak(self.conversational_memory.fallback_reply(patient_name))
            elif care_decision.principle == CarePrinciple.ONE_STEP_GUIDANCE and \
                    self.current_patient_state.mode == PatientStateMode.AWAITING_REMINDER:
                # Proactive scheduled reminder, at most once per reminder interval per dose.
                msg = self.due_reminder_message(patient_name)
                action = _speak(msg) if msg else None
            elif action is not None and care_decision.message_override:
                action = InteractionAction(type=action.type, message=care_decision.message_override)

            if action is not None:
                if u_speech or care_decision.action_type != "SILENCE":
                    actions.append(action)
                    # Physical Audio Output via Speaker HAL; record whether it succeeded.
                    if hasattr(action, "message") and action.message:
                        try:
                            self.last_speech_delivered = bool(self.runtime_manager.speaker.speak(action.message))
                        except Exception as speak_err:
                            self.last_speech_delivered = False
                            logger.warning(f"⚠️ [Speaker] Speech output failed: {speak_err}")
                # MEMORA's own replies are not stored as memories about the person (they
                # could later be recalled as if they were facts); the exchange is
                # recorded as an episode below.

            # Automatic Real Episode Generation into DB EpisodeRepository on runtime cycle
            episode_written = False
            try:
                from src.cognition.episode import Episode
                from datetime import datetime

                raw_objs = getattr(perception_context, "objects", []) or []
                det_objs = [getattr(o, "object_name", str(o)) for o in raw_objs]
                act_str = perception_context.activity if perception_context and hasattr(perception_context, "activity") else "Active observation"

                ep_summary = ""
                if u_speech:
                    ep_summary = f"User said: '{u_speech}'"
                    if action and hasattr(action, "message") and action.message:
                        ep_summary += f" | System responded: '{action.message}'"
                elif action and hasattr(action, "message") and action.message:
                    ep_summary = f"System: '{action.message}'"
                elif act_str:
                    ep_summary = f"Activity: {act_str}"
                    if det_objs:
                        ep_summary += f" (Observed objects: {', '.join(det_objs[:3])})"

                if ep_summary and self.database and hasattr(self.database, "episode_repo") and self.database.episode_repo:
                    ep = Episode(
                        person=p_name,
                        summary=ep_summary,
                        timestamp=datetime.now(),
                        location=loc_val,
                        commitments=[],
                        tags=[f"room:{loc_val}", f"activity:{act_str}"] + [f"object:{o}" for o in det_objs[:3]]
                             + (["speaker:self"] if getattr(event, "face_id", None) == "patient_self" else []),
                    )
                    self.database.episode_repo.add_episode(ep)
                    episode_written = True
                    logger.debug(f"📅 [Episode Logging] Persisted episode for {p_name}: '{ep_summary}' into database.")
            except Exception as ep_err:
                logger.warning(f"⚠️ [Episode Logging Error] Failed to persist episode: {ep_err}")
            total_latency = time.perf_counter() - cycle_start
            metrics.stop_timer("latency.cognition.total")

            # Only the measured total is reported. (Per-stage figures used to be printed
            # as fixed fractions of the total, which were not measurements.)
            self.last_cycle_latency_ms = total_latency * 1000.0

            # --------------------------------------------------
            # 7. Clinical Decision Trace & Audit Logging
            # --------------------------------------------------
            speech_produced = bool(action and hasattr(action, "message") and action.message and care_decision.action_type != "SILENCE")
            memory_written = episode_written  # true only if a record was actually persisted
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
            # Enrich trace with COS metadata
            self.latest_clinical_trace.working_memory_snapshot = self.cognitive_kernel.working_memory.snapshot()
            self.latest_clinical_trace.attention_focus = self.cognitive_kernel.attention_manager.get_current_focus().to_dict()
            self.latest_clinical_trace.cos_reasoning_path = cos_action.reasoning_path
            self.latest_clinical_trace.cos_action_type = cos_action.action_type.value
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
                outcome=("SPOKEN" if self.last_speech_delivered else "SPEECH_OUTPUT_FAILED") if actions else "SILENT",
            )

            from src.clinical.clinical_models import ConsentFeature
            clinical_context = {
                # Fictional profile defaults are only shown in demo mode.
                "patient_name": patient_name or None,
                "primary_caregiver": self.patient_profile_mgr.get_profile().primary_caregiver if self.demo_data else None,
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

            # Record Phase 22 Structured Audit Record
            self.latest_audit_record = self.audit_framework.record_audit(
                cycle_id=cycle_id,
                triggering_event=getattr(event, "type", "PERSON_ARRIVED").value if hasattr(getattr(event, "type", None), "value") else str(getattr(event, "type", "PERSON_ARRIVED")),
                active_goal=goal_hypotheses[0].name if goal_hypotheses else None,
                active_context_summary=f"Identity: {event.name or 'Unknown'}, Time: {c_time}, Room: {loc_val}",
                working_memory_keys=list(self.cognitive_kernel.working_memory.snapshot().get("slots", {}).keys()),
                selected_care_policy=care_decision.principle.value,
                evidence_summary=f"Advisory COS safety: {safety_eval.status.value}, Passed: {sum(1 for c in safety_eval.check_results if c.passed)}/{len(safety_eval.check_results)}",
                safety_status=safety_eval.status.value,
                safety_checks_passed=sum(1 for c in safety_eval.check_results if c.passed),
                safety_checks_failed=[c.check_name for c in safety_eval.check_results if not c.passed],
                proposed_action=cos_action.action_type.value,
                # What MEMORA actually did this cycle. The COS safety evaluation applies to
                # the kernel's proposed action and is advisory; it does not gate replies.
                final_action=("ESCALATE" if care_decision.principle == CarePrinciple.EMERGENCY_ESCALATION
                              else "SPEAK" if actions else "SILENCE"),
                explanation=f"Advisory COS safety evaluation (not applied to the reply): {safety_eval.evaluation_reason}",
                patient_name=patient_name or "Patient",
            )

            # --------------------------------------------------
            # 6.55 Long-Term Memory Consolidation & Recall
            # --------------------------------------------------
            memory_summary = self.ltm_memory_engine.process_cycle(
                user_speech=u_speech,
                location=loc_val,
            )

            # --------------------------------------------------
            # 6.6 Behaviour Intelligence & Longitudinal Analytics
            # --------------------------------------------------
            behaviour_summary = self.behaviour_manager.update_cycle(
                event_name=getattr(event, "name", None),
                location=loc_val,
                user_speech=u_speech,
                patient_state_mode=self.current_patient_state.mode.value,
                time_of_day=c_time,
            )

            # --------------------------------------------------
            # 6.7 Cognitive Reasoning & Multi-Modal Fusion
            # --------------------------------------------------
            reasoning_summary = self.reasoning_engine.reason(
                event_name=getattr(event, "name", None),
                location=loc_val,
                user_speech=u_speech,
                patient_state_mode=self.current_patient_state.mode.value,
                active_goal_name=goal_hypotheses[0].name if goal_hypotheses else None,
            )

            # --------------------------------------------------
            # 6.75 Semantic Knowledge Graph & World Model
            # --------------------------------------------------
            knowledge_summary = self.knowledge_engine.process_cycle(
                location=loc_val,
                active_person=getattr(event, "name", None),
            )

            # --------------------------------------------------
            # 6.8 Executive Planning & Adaptive Execution
            # --------------------------------------------------
            executive_summary = self.executive_engine.process_cycle(
                cognitive_context=cognitive_context,
                working_memory=self.cognitive_kernel.working_memory,
                patient_state=self.current_patient_state,
                reasoning_summary=reasoning_summary,
                behaviour_summary=behaviour_summary,
                location=loc_val,
                user_speech=u_speech,
                patient_state_mode=self.current_patient_state.mode.value,
                emergency_active=self.emergency_mgr.get_current_state().active,
                missed_medications=missed_meds,
            )

            # --------------------------------------------------
            # 6.9 Experience Learning & Knowledge Accumulation
            # --------------------------------------------------
            experience_summary = self.experience_engine.process_cycle(
                executive_summary=executive_summary,
                reasoning_summary=reasoning_summary,
                location=loc_val,
            )

            # --------------------------------------------------
            # 8. Emit to Experience Platform
            # --------------------------------------------------
            try:
                cos_summary = {
                    "working_memory": self.cognitive_kernel.working_memory.snapshot(),
                    "attention_focus": self.cognitive_kernel.attention_manager.get_current_focus().to_dict(),
                    "action_type": safety_eval.final_action.action_type.value,
                    "reasoning_path": safety_eval.final_action.reasoning_path,
                    "safety_status": safety_eval.status.value,
                    "safety_evaluation_reason": safety_eval.evaluation_reason,
                    "degradation_health": self.degradation_manager.get_status().overall_health,
                }
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
                    cos_summary=cos_summary,
                    behaviour_summary=behaviour_summary,
                    reasoning_summary=reasoning_summary,
                    executive_summary=executive_summary,
                    experience_summary=experience_summary,
                    knowledge_summary=knowledge_summary,
                    memory_summary=memory_summary,
                    runtime_engine_summary=runtime_engine_summary,
                )
                stream.emit(stream_event)
            except Exception:
                pass  # Never let stream emission crash the pipeline
            
        except Exception as e:
            self.last_cycle_error = repr(e)
            logger.exception("[CognitivePipeline] Cycle failed: %s", e)
            # Graceful degradation: If anything fails, don't crash the background thread.
            # We can optionally issue a generic error interaction or just fail silently.
            pass

        if return_dict:
            # Report what this cycle actually decided. Re-running recall here used to
            # override safety guidance and store user facts a second time.
            final_speech = actions[0].message if actions and getattr(actions[0], "message", None) else None
            return {
                "speech_response": final_speech,
                "executive_summary": executive_summary,
                "actions": actions,
            }

        return actions

    def _handle_contextual_recall(self, u_speech: Optional[str], event: Any, p_profile: Any,
                                  face_id: Optional[str] = None) -> Optional[str]:
        """Direct answer from conversational memory for what the person said, if any."""
        if not u_speech:
            return None
        return self.conversational_memory.respond(u_speech, face_id=face_id,
                                                  patient_name=self._patient_name())

    def due_reminder_message(self, patient_name: Optional[str] = None) -> Optional[str]:
        """
        Gentle reminder for overdue scheduled doses not reported taken today, at most
        once per reminder interval per dose. Returns None when nothing is due.
        """
        due = [m.medication_name for m in self.medication_mgr.get_missed_medications()]
        now_ts = time.time()
        fresh = [m for m in due if now_ts - self._last_reminder_at.get(m, 0.0) >= self.reminder_interval_s]
        if not fresh:
            return None
        for m in fresh:
            self._last_reminder_at[m] = now_ts
        from src.clinical.patient_state import PatientState
        state = PatientState(mode=PatientStateMode.AWAITING_REMINDER, confidence=0.95,
                             primary_need="Scheduled medication reminder", details={"medications": fresh})
        return self.care_policy_framework.evaluate_policy(state, patient_name=patient_name or "").message_override

    def _is_known_visitor_arrival(self, event: Any) -> bool:
        from src.interaction.events import PresenceEventType
        rel = (getattr(event, "relationship", None) or "").strip().lower()
        name = (getattr(event, "name", None) or "").strip()
        own_name = (self._patient_name() or "").strip().lower()
        return (getattr(event, "type", None) == PresenceEventType.PERSON_ARRIVED
                and bool(name)
                and rel not in ("patient", "self")
                and name.lower() != own_name)

    def _patient_name(self) -> str:
        """
        Name to address the person by: the name they gave MEMORA, else the
        profile name in demo mode, else no name at all.
        """
        stored = self.conversational_memory.get_preferred_name()
        if stored:
            return stored
        return self.patient_profile_mgr.get_profile().preferred_name if self.demo_data else ""

    @property
    def _search_history(self) -> list[dict]:
        return self.conversational_memory.search_history
