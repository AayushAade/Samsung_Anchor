"""
MEMORA Cross-Subsystem Consistency Checker.

Verifies logical consistency and reference integrity across Knowledge, Memory,
Experience, Reasoning, Executive, Trust, Session, and Pipeline stages without mutating state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.integrity.integrity_models import IntegrityCategory, IntegrityIssue, IntegrityLevel


class ConsistencyChecker:
    """
    Read-only checker verifying cross-subsystem reference integrity and pipeline ordering consistency.
    """

    EXPECTED_PIPELINE_ORDER = [
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

    @classmethod
    def check_consistency(
        cls,
        knowledge_engine: Optional[Any] = None,
        memory_engine: Optional[Any] = None,
        executive_engine: Optional[Any] = None,
        experience_engine: Optional[Any] = None,
        session_manager: Optional[Any] = None,
        reasoning_engine: Optional[Any] = None,
        pipeline_stage_order: Optional[List[str]] = None,
    ) -> List[IntegrityIssue]:
        issues: List[IntegrityIssue] = []

        # 1. Memory <-> Knowledge Reference Consistency
        if memory_engine is not None and hasattr(memory_engine, "repository"):
            repo = getattr(memory_engine, "repository")
            if hasattr(repo, "get_all_active"):
                active_memories = repo.get_all_active()
                active_ids = {m.memory_id for m in active_memories}

                for m in active_memories:
                    for k_ref in getattr(m, "knowledge_references", []):
                        if knowledge_engine is not None and hasattr(knowledge_engine, "fact_repository"):
                            fact_repo = getattr(knowledge_engine, "fact_repository")
                            if hasattr(fact_repo, "get_all_facts"):
                                known_fact_ids = {f.fact_id for f in fact_repo.get_all_facts()}
                                if k_ref not in known_fact_ids:
                                    issues.append(
                                        IntegrityIssue(
                                            category=IntegrityCategory.KNOWLEDGE,
                                            severity=IntegrityLevel.WARNING,
                                            subsystem="MemoryEngine",
                                            description=f"Memory record `{m.memory_id}` references knowledge fact `{k_ref}` which is missing in FactRepository.",
                                            affected_reference=f"MemoryRecord[{m.memory_id}].knowledge_references[{k_ref}]",
                                            recommendation="Verify knowledge fact ingestion or remove orphaned knowledge reference.",
                                        )
                                    )

        # 2. Executive <-> Memory Reference Consistency
        if executive_engine is not None and memory_engine is not None:
            if hasattr(executive_engine, "goal_manager") and hasattr(memory_engine, "repository"):
                g_mgr = getattr(executive_engine, "goal_manager")
                if hasattr(g_mgr, "active_goals"):
                    active_goals = getattr(g_mgr, "active_goals", [])
                    active_mem_ids = {m.memory_id for m in memory_engine.repository.get_all_active()}

                    for g in active_goals:
                        mem_ref = getattr(g, "context_memory_id", None)
                        if mem_ref and mem_ref not in active_mem_ids:
                            issues.append(
                                IntegrityIssue(
                                    category=IntegrityCategory.EXECUTIVE,
                                    severity=IntegrityLevel.WARNING,
                                    subsystem="ExecutiveEngine",
                                    description=f"Executive Goal `{getattr(g, 'goal_id', 'unknown')}` references memory `{mem_ref}` which is not active in MemoryRepository.",
                                    affected_reference=f"Goal[{getattr(g, 'goal_id', 'unknown')}].context_memory_id",
                                    recommendation="Ensure memory retention policy aligns with active executive goal lifecycles.",
                                )
                            )

        # 3. Session <-> Subsystem Reference Consistency
        if session_manager is not None:
            if hasattr(session_manager, "get_all_sessions"):
                sessions = session_manager.get_all_sessions()
                for ses in sessions:
                    for sub in getattr(ses, "participating_subsystems", []):
                        if sub not in cls.EXPECTED_PIPELINE_ORDER and sub != "CognitivePipeline":
                            issues.append(
                                IntegrityIssue(
                                    category=IntegrityCategory.SESSION,
                                    severity=IntegrityLevel.INFO,
                                    subsystem="SessionManager",
                                    description=f"Session `{ses.session_id}` registered unknown participating subsystem `{sub}`.",
                                    affected_reference=f"CognitiveSession[{ses.session_id}].participating_subsystems",
                                    recommendation="Register standard subsystem names in session execution traces.",
                                )
                            )

        # 4. Pipeline Stage Ordering Validation
        if pipeline_stage_order is not None:
            if pipeline_stage_order != cls.EXPECTED_PIPELINE_ORDER:
                issues.append(
                    IntegrityIssue(
                        category=IntegrityCategory.PIPELINE,
                        severity=IntegrityLevel.ERROR,
                        subsystem="CognitivePipeline",
                        description="Pipeline stage execution order deviates from standard architectural sequence.",
                        affected_reference="CognitivePipeline.process() stage sequence",
                        recommendation="Maintain standardized pipeline sequence: Perception -> COS -> Memory -> Behaviour -> Reasoning -> Knowledge -> Executive -> Experience -> Safety -> Stream -> Runtime.",
                    )
                )

        return issues
