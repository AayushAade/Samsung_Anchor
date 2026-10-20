"""
MEMORA Executive Risk Engine (Phase 10 — Objective 2).

Evaluates multi-factor risk scenarios for Alzheimer's patients:
- Repetitive queries -> Confusion elevation
- Dizziness / missed meals / medication history -> Fall & medical risk
- Night wandering / low lighting -> Fall & disorientation risk
- Repeated medicine search -> Medication adherence / overdose risk

Classifies risk level into LOW, MEDIUM, HIGH, CRITICAL with explicit justifications.
"""

from __future__ import annotations

from typing import Any, List, Optional
from src.executive.executive_models import RiskAssessment, RiskLevel, Situation


class ExecutiveRiskEngine:
    """
    Evaluates clinical and situational risk factors to govern executive decisions.
    """

    @classmethod
    def evaluate_risk(
        cls,
        situation: Situation,
        emergency_active: bool = False,
        missed_medications: Optional[List[str]] = None,
        user_speech: Optional[str] = None,
    ) -> RiskAssessment:
        factors: List[str] = []
        score = 0.05
        justifications: List[str] = []

        # 1. Emergency Alert Override -> CRITICAL
        if emergency_active:
            factors.append("Emergency Alert Active")
            score = 1.0
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                score=1.0,
                factors=factors,
                justification="Active medical emergency alert requires immediate safety response."
            )

        # 2. Night Wandering & Fall Risk
        if situation.is_night and situation.activity in ("Walking", "Pacing", "Searching"):
            factors.append("Night Wandering / Fall Risk")
            score += 0.35
            justifications.append("Walking at night in low lighting increases fall and disorientation risk.")

        # 3. Repeated Questioning & High Confusion
        if situation.repeating_question or situation.question_count >= 3:
            factors.append(f"High Repetition (Count: {situation.question_count})")
            score += min(0.30, situation.question_count * 0.10)
            justifications.append(f"Repeated questioning ({situation.question_count}x) indicates severe confusion or distress.")

        # 4. Medication Search / Adherence Risk
        if situation.pending_medication or (missed_medications and len(missed_medications) > 0):
            factors.append("Pending / Missed Medication")
            score += 0.25
            justifications.append("Unresolved medication schedule poses adherence and clinical safety risk.")

        if situation.searching_activity and situation.search_target and "medicine" in situation.search_target.lower():
            factors.append("Repeated Medication Searching")
            score += 0.30
            justifications.append("Searching repeatedly for medicine creates potential overdose risk requiring supervision.")

        # 5. Symptom Mentions in User Speech (Dizziness, Fall, Pain)
        if user_speech:
            u_lower = user_speech.lower()
            if any(sym in u_lower for sym in ("dizzy", "faint", "fell", "headache", "chest pain", "can't breathe")):
                factors.append("Clinical Symptom Utterance")
                score += 0.45
                justifications.append(f"Patient reported clinical symptom: '{user_speech}'. Immediate clinical evaluation warranted.")

        # Determine Risk Level
        score = round(min(1.0, score), 3)
        if score >= 0.75:
            level = RiskLevel.CRITICAL
        elif score >= 0.50:
            level = RiskLevel.HIGH
        elif score >= 0.25:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        justification_text = " ".join(justifications) if justifications else "Baseline clinical risk within normal limits."

        return RiskAssessment(
            level=level,
            score=score,
            factors=factors,
            justification=justification_text,
        )
