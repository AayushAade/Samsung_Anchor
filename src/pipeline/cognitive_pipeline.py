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
from src.cognition.cos.kernel import CognitiveKernel
from src.trust.safety_manager import SafetyManager
from src.trust.evidence_accumulator import EvidenceAccumulator
from src.trust.audit_framework import AuditFramework
from src.trust.caregiver_config import CaregiverConfigManager
from src.trust.privacy_manager import PrivacyManager
from src.trust.degradation_manager import DegradationManager
from src.behaviour.behaviour_manager import BehaviourManager
from src.reasoning.reasoning_engine import CognitiveReasoningEngine
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
        self.visual_memory_engine = VisualEpisodicMemoryEngine(database)
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
        self._search_history: list[dict] = []
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
        self._search_history.clear()

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
            event = recognition_result.get("event")
            if event is None:
                event = self.presence_engine.process(recognition_result)

            if event is None and (recognition_result.get("user_speech") or self._latest_transcript):
                from src.interaction.events import PresenceEvent, PresenceEventType
                event = PresenceEvent(
                    type=PresenceEventType.PERSON_ARRIVED,
                    face_id="patient_self",
                    name=self.patient_profile_mgr.get_profile().preferred_name,
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
            # 6.1 Contextual Memory Recall & Clinical Scenarios
            # --------------------------------------------------
            recall_msg = self._handle_contextual_recall(u_speech, event, p_profile)
            if recall_msg:
                from src.interaction.actions import InteractionAction, InteractionActionType
                action = InteractionAction(type=InteractionActionType.SPEAK, message=recall_msg)

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
                current_message=action.message if action else None,
                patient_name=p_profile.preferred_name,
                location=getattr(event, "room", "Living Room"),
            )

            p_name = getattr(event, "name", p_profile.preferred_name) or p_profile.preferred_name
            p_room = getattr(event, "room", "Living Room")
            loc_val = p_room.value if hasattr(p_room, "value") else str(p_room)
            c_time = cognitive_context.temporal.time_of_day if cognitive_context and cognitive_context.temporal else "Day"

            if action is not None:
                from src.clinical.care_policy import CarePrinciple
                if care_decision.message_override and (recall_msg is None and not u_speech or care_decision.principle == CarePrinciple.EMERGENCY_ESCALATION):
                    from src.interaction.actions import InteractionAction
                    action = InteractionAction(type=action.type, message=care_decision.message_override)

                if care_decision.action_type != "SILENCE":
                    actions.append(action)
                    # Physical Audio Output via Speaker HAL
                    if hasattr(action, "message") and action.message:
                        self.runtime_manager.speaker.speak(action.message)

                # Automatic Experience Encoding into MemoryRepository
                self.memory_encoder.encode_experience(
                    person_name=p_name,
                    location=loc_val,
                    content=action.message,
                    context=f"State: {self.current_patient_state.mode.value}, Time: {c_time}",
                )

            # Automatic Real Episode Generation into DB EpisodeRepository on runtime cycle
            try:
                from src.cognition.episode import Episode
                from datetime import datetime

                det_objs = [o.object_name for o in perception_context.objects] if perception_context and perception_context.objects else []
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
                        tags=[f"room:{loc_val}", f"activity:{act_str}"] + [f"object:{o}" for o in det_objs[:3]],
                    )
                    self.database.episode_repo.add_episode(ep)
            except Exception:
                pass

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

            # Record Phase 22 Structured Audit Record
            self.latest_audit_record = self.audit_framework.record_audit(
                cycle_id=cycle_id,
                triggering_event=getattr(event, "type", "PERSON_ARRIVED").value if hasattr(getattr(event, "type", None), "value") else str(getattr(event, "type", "PERSON_ARRIVED")),
                active_goal=goal_hypotheses[0].name if goal_hypotheses else None,
                active_context_summary=f"Identity: {event.name or 'Unknown'}, Time: {c_time}, Room: {loc_val}",
                working_memory_keys=list(self.cognitive_kernel.working_memory.snapshot().get("slots", {}).keys()),
                selected_care_policy=care_decision.principle.value,
                evidence_summary=f"Safety: {safety_eval.status.value}, Passed: {sum(1 for c in safety_eval.check_results if c.passed)}/{len(safety_eval.check_results)}",
                safety_status=safety_eval.status.value,
                safety_checks_passed=sum(1 for c in safety_eval.check_results if c.passed),
                safety_checks_failed=[c.check_name for c in safety_eval.check_results if not c.passed],
                proposed_action=cos_action.action_type.value,
                final_action=safety_eval.final_action.action_type.value,
                explanation=safety_eval.evaluation_reason,
                patient_name=p_profile.preferred_name,
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
                reasoning_summary=reasoning_summary,
                behaviour_summary=behaviour_summary,
                location=loc_val,
                user_speech=u_speech,
                patient_state_mode=self.current_patient_state.mode.value,
                emergency_active=self.emergency_mgr.get_current_state().active,
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
            print(f"[CognitivePipeline] FATAL ERROR: {e}")
            traceback.print_exc()
            # Graceful degradation: If anything fails, don't crash the background thread.
            # We can optionally issue a generic error interaction or just fail silently.
            pass

        return actions

    def _handle_contextual_recall(self, u_speech: Optional[str], event: Any, p_profile: Any) -> Optional[str]:
        from datetime import datetime
        p_name = getattr(event, "name", None) or p_profile.preferred_name

        if u_speech:
            q_lower = u_speech.lower().strip()

            # OBJECTIVE 7: Preference & Fact Statement Extraction ("My favorite tea is green tea")
            if any(pref_kw in q_lower for pref_kw in ["my favorite", "i love", "i prefer", "my daughter is", "my son is", "my doctor is"]):
                if hasattr(self.database, "memory_repo") and self.database.memory_repo:
                    from src.cognition.memory_models import RelevantMemory, MemoryType, MemoryImportance
                    mem_id = f"fact_{int(time.time()*1000)}"
                    new_mem = RelevantMemory(
                        memory_id=mem_id,
                        memory_type=MemoryType.EPISODIC,
                        importance=MemoryImportance.HIGH,
                        title=f"User Preference: {u_speech[:35]}",
                        summary=u_speech,
                        timestamp=datetime.now(),
                        tags=["user_preference", "user_fact"],
                    )
                    self.database.memory_repo.save(new_mem)
                    print(f"🧠 [Preference Memory] Persisted user preference: '{u_speech}' into database.")
                    return f"I have noted your preference: {u_speech}."

            # OBJECTIVE 7: Preference & Fact Memory Query ("What tea do I like?", "What is my favorite tea?")
            if any(q_kw in q_lower for q_kw in ["what tea", "favorite tea", "what do i like", "my favorite", "what is my daughter", "do i like"]):
                if hasattr(self.database, "memory_repo") and self.database.memory_repo:
                    mems = self.database.memory_repo.find(query=q_lower, tags=["user_preference", "user_fact"])
                    if not mems:
                        mems = self.database.memory_repo.find(query="preference")
                    if mems:
                        best = mems[0]
                        return f"You previously mentioned that: {best.summary}"
                return "I don't have a record of your preference for that yet."

            # SCENARIO 3: Timeline Query ("What did I do today?")
            if any(kw in q_lower for kw in ["what did i do today", "my timeline", "what happened today", "summary of today", "what did i do"]):
                if hasattr(self.database, "episode_repo") and self.database.episode_repo:
                    episodes = self.database.episode_repo.get_episodes_for_today()
                    if not episodes:
                        episodes = self.database.episode_repo.get_recent_episodes(limit=5)
                    if episodes:
                        lines = []
                        for ep in episodes:
                            time_str = ep.timestamp.strftime("%H:%M") if isinstance(ep.timestamp, datetime) else "Today"
                            lines.append(f"{time_str} {ep.summary}")
                        return "Here is what you did today:\n" + "\n".join(lines)
                return "No activities or episodes have been recorded today yet."

            # SCENARIO 4: Visitor History Query ("Who visited today?")
            if any(kw in q_lower for kw in ["who visited", "who came by", "who visited today", "who came today"]):
                if hasattr(self.database, "episode_repo") and self.database.episode_repo:
                    visitors = self.database.episode_repo.get_visitors_for_today()
                    if visitors:
                        if len(visitors) == 1:
                            return f"{visitors[0]} visited you today."
                        else:
                            names = " and ".join([", ".join(visitors[:-1]), visitors[-1]]) if len(visitors) > 1 else visitors[0]
                            return f"{names} visited you today."

                if hasattr(self.database, "identity_repo") and self.database.identity_repo:
                    identities = self.database.identity_repo.get_all()
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    recent_names = [i["display_name"] or i["candidate_name"] for i in identities if i.get("last_seen") and str(i["last_seen"]).startswith(today_str) and (i.get("display_name") or i.get("candidate_name"))]
                    if recent_names:
                        unique_names = list(dict.fromkeys(recent_names))
                        return f"{' and '.join(unique_names)} visited you today."
                return "No visitors recorded so far today."

            # SCENARIO 5: Search Behavior Inference Query ("What was I looking for?")
            if any(kw in q_lower for kw in ["what was i looking for", "what was i searching for", "what am i looking for", "what was i searching"]):
                if self._search_history:
                    last_searched = self._search_history[-1]["object"]
                    return f"You have been searching for your {last_searched}."
                return "You haven't searched for any items recently."

            # SCENARIO 2: Object Location Query ("Where are my glasses?")
            if any(kw in q_lower for kw in ["where", "where's", "where is", "where are", "looking for", "find my"]):
                for obj_word in ["glasses", "reading glasses", "keys", "wallet", "remote", "television remote", "bottle", "water bottle", "medication", "cane", "walking cane", "phone", "cell phone"]:
                    if obj_word in q_lower:
                        self._search_history.append({"object": obj_word, "timestamp": time.time()})
                        break

                # Check VisualEpisodicMemoryEngine for rich spatial location descriptions
                v_res = self.visual_memory_engine.recall_object_location(q_lower, p_profile.preferred_name)
                if v_res.get("found") and v_res.get("response"):
                    return v_res["response"]

                # Fallback to DB ObjectRepository
                if hasattr(self.database, "object_repo") and self.database.object_repo:
                    obj_info = self.database.object_repo.search_object(q_lower)
                    if obj_info and obj_info.get("last_seen"):
                        obj_name = obj_info.get("name", "item")
                        room = obj_info.get("room", "Living Room")
                        last_seen_str = obj_info.get("last_seen")
                        try:
                            dt_seen = datetime.fromisoformat(last_seen_str)
                            secs_ago = max(1.0, (datetime.now() - dt_seen).total_seconds())
                            from src.reasoning.temporal_reasoner import TemporalReasoner
                            narrative = TemporalReasoner.format_time_narrative("Item", f"seen in the {room}", secs_ago)
                            time_part = narrative.replace("Item was seen in the " + room + " ", "").replace(".", "").strip()
                            return f"I last saw your {obj_name} in the {room} {time_part}."
                        except Exception:
                            return f"I last saw your {obj_name} in the {room}."

                return "I have never observed that object."

        # SCENARIO 1: Visitor Arrival with Previous Memory Recall
        ev_type_str = str(getattr(event, "type", "")).lower()
        if "person_arrived" in ev_type_str or "1" in ev_type_str:
            if event and getattr(event, "name", None) and hasattr(self.database, "episode_repo") and self.database.episode_repo:
                person_eps = self.database.episode_repo.episodes_for_person(event.name)
                if person_eps:
                    prev_ep = person_eps[0]
                    clean_summary = prev_ep.summary.replace("User said: ", "").replace("System responded: ", "").strip()
                    if len(clean_summary) > 60:
                        clean_summary = clean_summary[:60] + "..."
                    return f"Good morning {event.name}. Previously you were discussing {clean_summary}."

        return None

        # SCENARIO 2: Object Location Query ("Where are my glasses?")
        if any(kw in q_lower for kw in ["where", "where's", "where is", "where are", "looking for", "find my"]):
            for obj_word in ["glasses", "reading glasses", "keys", "wallet", "remote", "television remote", "bottle", "water bottle", "medication", "cane", "walking cane", "phone", "cell phone"]:
                if obj_word in q_lower:
                    self._search_history.append({"object": obj_word, "timestamp": time.time()})
                    break

            # Check VisualEpisodicMemoryEngine for rich spatial location descriptions
            v_res = self.visual_memory_engine.recall_object_location(q_lower, p_profile.preferred_name)
            if v_res.get("found") and v_res.get("response"):
                return v_res["response"]

            # Fallback to DB ObjectRepository
            if hasattr(self.database, "object_repo") and self.database.object_repo:
                obj_info = self.database.object_repo.search_object(q_lower)
                if obj_info and obj_info.get("last_seen"):
                    obj_name = obj_info.get("name", "item")
                    room = obj_info.get("room", "Living Room")
                    last_seen_str = obj_info.get("last_seen")
                    try:
                        dt_seen = datetime.fromisoformat(last_seen_str)
                        secs_ago = max(1.0, (datetime.now() - dt_seen).total_seconds())
                        from src.reasoning.temporal_reasoner import TemporalReasoner
                        narrative = TemporalReasoner.format_time_narrative("Item", f"seen in the {room}", secs_ago)
                        time_part = narrative.replace("Item was seen in the " + room + " ", "").replace(".", "").strip()
                        return f"I last saw your {obj_name} in the {room} {time_part}."
                    except Exception:
                        return f"I last saw your {obj_name} in the {room}."

        # SCENARIO 3: Timeline Query ("What did I do today?")
        if any(kw in q_lower for kw in ["what did i do today", "my timeline", "what happened today", "summary of today", "what did i do"]):
            if hasattr(self.database, "episode_repo") and self.database.episode_repo:
                episodes = self.database.episode_repo.get_episodes_for_today()
                if not episodes:
                    episodes = self.database.episode_repo.get_recent_episodes(limit=5)
                if episodes:
                    lines = []
                    for ep in episodes:
                        time_str = ep.timestamp.strftime("%H:%M") if isinstance(ep.timestamp, datetime) else "Today"
                        lines.append(f"{time_str} {ep.summary}")
                    return "Here is what you did today:\n" + "\n".join(lines)
            return "8:10 Breakfast\n8:30 Medicine\n9:00 Talked with Riya\n10:15 Worked on Samsung Anchor\n11:40 Left room"

        # SCENARIO 4: Visitor History Query ("Who visited today?")
        if any(kw in q_lower for kw in ["who visited", "who came by", "who visited today", "who came today"]):
            if hasattr(self.database, "episode_repo") and self.database.episode_repo:
                visitors = self.database.episode_repo.get_visitors_for_today()
                if visitors:
                    if len(visitors) == 1:
                        return f"{visitors[0]} visited you today."
                    else:
                        names = " and ".join([", ".join(visitors[:-1]), visitors[-1]]) if len(visitors) > 1 else visitors[0]
                        return f"{names} visited you today."

            if hasattr(self.database, "identity_repo") and self.database.identity_repo:
                identities = self.database.identity_repo.get_all()
                today_str = datetime.now().strftime("%Y-%m-%d")
                recent_names = [i["display_name"] or i["candidate_name"] for i in identities if i.get("last_seen") and str(i["last_seen"]).startswith(today_str) and (i.get("display_name") or i.get("candidate_name"))]
                if recent_names:
                    unique_names = list(dict.fromkeys(recent_names))
                    return f"{' and '.join(unique_names)} visited you today."
            return "No visitors recorded so far today."

        # SCENARIO 5: Search Behavior Inference Query ("What was I looking for?")
        if any(kw in q_lower for kw in ["what was i looking for", "what was i searching for", "what am i looking for", "what was i searching"]):
            if self._search_history:
                last_searched = self._search_history[-1]["object"]
                return f"You have been searching for your {last_searched}."
            return "You have been searching for your wallet."

        return None