"""
MEMORA Explainable AI & Memory Provenance Engine.

Translates complex perception and cognitive states into human-readable,
clinically grounded explanations while enforcing zero-hallucination safety rules.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from src.clinical.decision_timeline import ConfidenceLevel


@dataclass
class MemoryProvenance:
    """
    Metadata tracking the origin and clinical relevance of a retrieved memory.
    """
    origin: str                             # e.g., "Visual Room Perception" or "Caregiver Profile Input"
    time_stored_iso: str                    # ISO timestamp
    evidence_source: str                    # e.g., "Webcam Camera Device Index 0"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    clinical_relevance: str = "High"        # Clinical importance descriptor

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin,
            "time_stored": self.time_stored_iso,
            "evidence_source": self.evidence_source,
            "confidence": self.confidence.value,
            "clinical_relevance": self.clinical_relevance,
        }


class ExplainabilityEngine:
    """
    Generates non-technical, human-readable explainability strings
    and enforces cognitive safety rules to prevent memory or identity hallucinations.
    """

    @staticmethod
    def explain_identity_match(name: str | None, confidence_score: float, is_confirmed: bool = True) -> str:
        """
        Generate human-friendly explanation for face recognition results.
        Never exposes raw float vectors or cosine similarity math.
        """
        level = ConfidenceLevel.from_score(confidence_score)
        if not name or level == ConfidenceLevel.UNCERTAIN:
            return "Unable to confirm identity with sufficient certainty. Operating in gentle observational mode."

        if is_confirmed:
            return f"Recognized {name} ({level.value}) based on confirmed family relationship profile."
        return f"Identified visitor as {name} ({level.value}) based on previous visual observations."

    @staticmethod
    def explain_memory_retrieval(
        item_name: str,
        found: bool,
        location: str | None = None,
        provenance: MemoryProvenance | None = None,
    ) -> str:
        """
        Generate human-friendly explanation for visual memory item recall.
        Enforces strict non-hallucination refusal when item is not in spatial memory.
        """
        if not found or not location:
            return f"I haven't seen your {item_name} recently. I will keep an eye out for them in the room."

        prov_str = f" (Observed by {provenance.origin} at {provenance.time_stored_iso})" if provenance else ""
        return f"Your {item_name} is located at {location}{prov_str}."

    @staticmethod
    def explain_care_policy(patient_mode: str, selected_policy: str) -> str:
        """
        Explain clinical policy selection in terms of patient emotional state.
        """
        explanations = {
            "VALIDATION_THERAPY": "Applied Validation Therapy to validate feelings and reduce anxiety.",
            "ONE_STEP_GUIDANCE": "Applied One-Step Guidance to provide clear, concise direction.",
            "REPETITIVE_REDIRECTION": "Applied Repetitive Redirection to give reassuring, consistent answers.",
            "SUPPORTIVE_SILENCE": "Applied Supportive Silence to allow calm observation without unnecessary interruption.",
            "EMERGENCY_ESCALATION": "Applied Emergency Escalation to alert caregiver team of safety hazard.",
        }
        return explanations.get(selected_policy, f"Selected {selected_policy} based on {patient_mode} patient state.")

    @staticmethod
    def apply_cognitive_safety_checks(
        candidate_identity: str | None, confidence_score: float
    ) -> tuple[str | None, bool, str]:
        """
        Enforce cognitive safety rules.

        Returns
        -------
        tuple[str | None, bool, str]
            Tuple of (safe_identity_name, is_safe, rationale_string)
        """
        level = ConfidenceLevel.from_score(confidence_score)

        if confidence_score < 0.50 or level == ConfidenceLevel.UNCERTAIN:
            return (
                None,
                False,
                "SAFETY RULE ENFORCED: Low match confidence. Suppressing identity assignment to prevent false identity hallucination.",
            )

        return (
            candidate_identity,
            True,
            f"SAFETY CHECK PASSED: Match confidence ({level.value}) satisfies clinical safety threshold.",
        )
