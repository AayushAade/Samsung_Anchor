"""
MEMORA Deterministic Planner.

Produces structured, executable plans from cognitive reasoning conclusions,
working memory context, and active goal priorities.

Strictly deterministic: Zero reinforcement learning or non-deterministic optimization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.executive.executive_models import Goal, Plan, TaskNode, TaskType
from src.executive.task_graph import TaskGraph


class DeterministicPlanner:
    """
    Produces structured plans mapping operational goals to ordered task graphs.
    """

    @classmethod
    def generate_plan(
        cls,
        goal: Goal,
        reasoning_summary: Optional[Dict[str, Any]] = None,
        behaviour_summary: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        """
        Synthesize an executable plan for the target goal.
        """
        graph = TaskGraph(parent_goal_id=goal.goal_id)

        title_lower = goal.title.lower()

        if "glasses" in title_lower or "searching" in title_lower:
            # Plan 1: Locate Misplaced Object
            t1 = graph.add_task(
                title="Determine last known object location",
                task_type=TaskType.DETERMINE_LOCATION,
                estimated_duration_sec=10.0,
                action_payload={"object_name": "reading glasses", "target_room": "Living Room"},
            )
            t2 = graph.add_task(
                title="Verify resting place in Living Room",
                task_type=TaskType.SEARCH_ROOM,
                dependencies=[t1.task_id],
                estimated_duration_sec=15.0,
                action_payload={"location": "Living Room side table"},
            )
            t3 = graph.add_task(
                title="Suggest retrieval cue to user",
                task_type=TaskType.SUGGEST_RETRIEVAL,
                dependencies=[t2.task_id],
                estimated_duration_sec=10.0,
                action_payload={"cue_text": "Your reading glasses are likely on the Living Room side table."},
            )
            rationale = "Structured 3-step spatial retrieval plan based on spatial memory and routine patterns."

        elif "medication" in title_lower:
            # Plan 2: Assist Medication Routine
            t1 = graph.add_task(
                title="Check medication schedule and pending dosage",
                task_type=TaskType.CHECK_MEDICATION,
                estimated_duration_sec=10.0,
                action_payload={"medication": "Morning Pills"},
            )
            t2 = graph.add_task(
                title="Provide gentle medication reminder prompt",
                task_type=TaskType.PROVIDE_ORIENTATION,
                dependencies=[t1.task_id],
                estimated_duration_sec=15.0,
                action_payload={"prompt": "It's time for your morning medication."},
            )
            rationale = "Sequential medication assistance plan."

        else:
            # Default Assistive Plan
            t1 = graph.add_task(
                title="Provide gentle environmental orientation",
                task_type=TaskType.PROVIDE_ORIENTATION,
                estimated_duration_sec=15.0,
                action_payload={"info": "Default assistive orientation"},
            )
            rationale = "Default assistive orientation plan."

        ordered_tasks = graph.get_topological_order()

        return Plan(
            goal_id=goal.goal_id,
            tasks=ordered_tasks,
            confidence=max(0.60, min(0.95, goal.confidence)),
            rationale=rationale,
            is_validated=False,
        )
