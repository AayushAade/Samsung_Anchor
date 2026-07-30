"""
MEMORA Primary Integrity Validator.

Validates subsystem availability, ICognitiveSubsystem interface compliance,
subsystem registration completeness, and pipeline contract integrity without mutating state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.integrity.integrity_models import IntegrityCategory, IntegrityIssue, IntegrityLevel


REQUIRED_SUBSYSTEM_ATTRIBUTES = [
    ("perception_manager", "PerceptionManager"),
    ("presence_engine", "PresenceEngine"),
    ("cognitive_kernel", "CognitiveKernel"),
    ("memory_engine", "MemoryEngine"),
    ("behaviour_manager", "BehaviourManager"),
    ("reasoning_engine", "CognitiveReasoningEngine"),
    ("knowledge_engine", "KnowledgeEngine"),
    ("executive_engine", "ExecutiveEngine"),
    ("experience_engine", "ExperienceEngine"),
    ("central_runtime", "CentralRuntimeEngine"),
    ("session_engine", "SessionEngine"),
]


class IntegrityValidator:
    """
    Read-only validator verifying subsystem interfaces, registrations, and structural contracts.
    """

    @classmethod
    def validate_subsystems(
        cls,
        pipeline: Optional[Any] = None,
        service_registry: Optional[Any] = None,
        custom_subsystems: Optional[Dict[str, Any]] = None,
    ) -> List[IntegrityIssue]:
        issues: List[IntegrityIssue] = []

        # 1. Pipeline Contract & Subsystem Attribute Validation
        if pipeline is not None:
            for attr_name, sub_label in REQUIRED_SUBSYSTEM_ATTRIBUTES:
                if not hasattr(pipeline, attr_name) or getattr(pipeline, attr_name) is None:
                    issues.append(
                        IntegrityIssue(
                            category=IntegrityCategory.PIPELINE,
                            severity=IntegrityLevel.CRITICAL,
                            subsystem="CognitivePipeline",
                            description=f"Required pipeline subsystem component '{sub_label}' (attribute '{attr_name}') is missing or uninstantiated.",
                            affected_reference=f"CognitivePipeline.{attr_name}",
                            recommendation=f"Instantiate and assign {sub_label} to pipeline attribute '{attr_name}'.",
                        )
                    )

        # 2. Service Registry Availability & Interface Compliance Validation
        if service_registry is not None:
            if hasattr(service_registry, "get_all_services"):
                services = service_registry.get_all_services()
                seen_ids = set()

                for s_name, service_inst in services.items():
                    # Duplicate check
                    if s_name in seen_ids:
                        issues.append(
                            IntegrityIssue(
                                category=IntegrityCategory.RUNTIME,
                                severity=IntegrityLevel.ERROR,
                                subsystem="ServiceRegistry",
                                description=f"Duplicate service registration detected for service identifier '{s_name}'.",
                                affected_reference=f"ServiceRegistry[{s_name}]",
                                recommendation="Ensure service names registered in ServiceRegistry are unique.",
                            )
                        )
                    seen_ids.add(s_name)

                    # Interface compliance check
                    if not isinstance(service_inst, ICognitiveSubsystem):
                        issues.append(
                            IntegrityIssue(
                                category=IntegrityCategory.RUNTIME,
                                severity=IntegrityLevel.WARNING,
                                subsystem=s_name,
                                description=f"Registered service '{s_name}' does not implement the standard ICognitiveSubsystem interface.",
                                affected_reference=f"ServiceRegistry[{s_name}]",
                                recommendation="Inherit from ICognitiveSubsystem base class to ensure standardized health, metrics, and lifecycle methods.",
                            )
                        )

        # 3. Custom Subsystems Map Validation
        if custom_subsystems:
            for name, inst in custom_subsystems.items():
                if inst is None:
                    issues.append(
                        IntegrityIssue(
                            category=IntegrityCategory.RUNTIME,
                            severity=IntegrityLevel.ERROR,
                            subsystem=name,
                            description=f"Custom cognitive subsystem entry '{name}' provided as None.",
                            affected_reference=f"Subsystems[{name}]",
                            recommendation="Provide non-null subsystem instance.",
                        )
                    )

        return issues
