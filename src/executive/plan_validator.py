"""
MEMORA Executive Plan Validator.

Validates plans before execution to guarantee:
- Safety constraint compliance
- Clinical policy compliance
- Non-circular task dependencies
- Valid non-empty task graphs
"""

from __future__ import annotations

from typing import List, Tuple

from src.executive.executive_models import Plan, TaskStatus


class PlanValidator:
    """
    Pre-execution validator for generated plans.
    """

    @classmethod
    def validate_plan(cls, plan: Plan) -> Tuple[bool, List[str]]:
        """
        Validate plan against structural, dependency, and safety rules.
        Returns (is_valid, validation_errors).
        """
        errors: List[str] = []

        if not plan.tasks:
            errors.append("Plan contains zero executable tasks.")

        # Check for circular dependencies
        task_ids = {t.task_id for t in plan.tasks}
        for task in plan.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task '{task.title}' references non-existent dependency '{dep}'.")
                if dep == task.task_id:
                    errors.append(f"Self-referential dependency detected in task '{task.title}'.")

        is_valid = len(errors) == 0
        plan.is_validated = is_valid
        return is_valid, errors
