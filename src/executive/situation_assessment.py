"""
MEMORA Situation Assessment Engine (Phase 10 — Objective 1).

Every cycle, synthesizes raw multimodal inputs (perception, working memory,
temporal context, goals, conversation, attention priorities, and patient state)
into ONE structured, immutable Situation world state object.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from src.executive.executive_models import Situation


class SituationAssessor:
    """
    Evaluates current system signals to produce a unified Situation world state.
    """

    @classmethod
    def assess_situation(
        cls,
        cognitive_context: Optional[Any] = None,
        working_memory: Optional[Any] = None,
        patient_state: Optional[Any] = None,
        user_speech: Optional[str] = None,
        location: str = "Living Room",
        time_of_day: str = "Day",
    ) -> Situation:
        patient_name = "Patient"
        detected_people = []
        detected_objects = []
        activity = "Sitting"
        is_night = time_of_day in ("Night", "Late Night", "Evening")
        repeating_q = False
        q_count = 0
        searching = False
        search_target = None
        pending_meds = False
        confusion = 0.10
        anxiety = 0.10

        # Extract Working Memory signals
        if working_memory:
            if hasattr(working_memory, "recall"):
                search_target = working_memory.recall("active_search_target")
                wm_people = working_memory.recall("current_people")
                if wm_people and isinstance(wm_people, list):
                    detected_people.extend(wm_people)
                wm_objs = working_memory.recall("current_detected_objects")
                if wm_objs and isinstance(wm_objs, list):
                    detected_objects.extend(wm_objs)
                topic = working_memory.recall("current_topic")
                if topic and "searching" in str(topic).lower():
                    searching = True
            elif isinstance(working_memory, dict):
                search_target = working_memory.get("active_search_target")

        if search_target:
            searching = True

        # Extract Speech signals
        if user_speech:
            u_lower = user_speech.lower()
            if any(kw in u_lower for kw in ("where is", "where are", "looking for", "find my", "lost my", "need my")):
                searching = True
            if any(kw in u_lower for kw in ("medicine", "pill", "medication")):
                pending_meds = True
            if any(kw in u_lower for kw in ("dizzy", "confused", "scared", "worried", "lost")):
                anxiety += 0.30
                confusion += 0.30

        # Extract Cognitive Context signals
        if cognitive_context:
            if getattr(cognitive_context, "identity", None) and getattr(cognitive_context.identity, "name", None):
                patient_name = cognitive_context.identity.name
            if getattr(cognitive_context, "temporal", None) and getattr(cognitive_context.temporal, "time_of_day", None):
                time_of_day = cognitive_context.temporal.time_of_day
                is_night = time_of_day in ("Night", "Late Night", "Evening")

        # Extract Patient State signals
        if patient_state:
            mode_str = getattr(getattr(patient_state, "mode", None), "value", "Calm")
            if "Anxious" in mode_str or "Distressed" in mode_str:
                anxiety = max(anxiety, 0.70)
            if "Confused" in mode_str:
                confusion = max(confusion, 0.70)
            if hasattr(patient_state, "repetition_count"):
                q_count = patient_state.repetition_count
                if q_count >= 2:
                    repeating_q = True
                    confusion += min(0.30, q_count * 0.10)

        return Situation(
            patient_name=patient_name,
            time_of_day=time_of_day,
            current_location=location,
            detected_people=list(dict.fromkeys(detected_people)),
            detected_objects=list(dict.fromkeys(detected_objects)),
            activity=activity,
            is_night=is_night,
            repeating_question=repeating_q,
            question_count=q_count,
            searching_activity=searching,
            search_target=search_target,
            pending_medication=pending_meds,
            confusion_score=min(1.0, confusion),
            anxiety_level=min(1.0, anxiety),
        )
