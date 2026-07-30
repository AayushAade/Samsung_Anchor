"""
MEMORA Execution History Index & Query Interface.

Provides structured timeline indexing and historical execution queries for:
- Room environment context
- Caregiver involvement
- Similar goal patterns
- Markdown timeline formatting
"""

from __future__ import annotations

from typing import List, Optional

from src.experience.experience_models import ExecutionOutcome, ExecutionRecord
from src.experience.experience_repository import ExperienceRepository


class ExecutionHistoryIndex:
    """
    Timeline index and query engine over ExperienceRepository.
    """

    def __init__(self, repository: ExperienceRepository) -> None:
        self.repository = repository

    def query_similar_executions(
        self, goal_title_keyword: str, limit: int = 5
    ) -> List[ExecutionRecord]:
        """
        Retrieve historical execution records matching a goal title keyword.
        """
        all_recs = self.repository.get_all_records()
        kw_lower = goal_title_keyword.lower()
        matched = [
            r for r in all_recs
            if any(kw_lower in t.get("title", "").lower() for t in r.tasks_executed)
            or kw_lower in r.goal_id.lower()
        ]
        return matched[-limit:]

    def generate_markdown_timeline(self, limit: int = 15) -> str:
        """
        Generate formatted Markdown summary table of historical executions.
        """
        records = self.repository.get_recent_records(limit=limit)
        if not records:
            return "No historical execution records logged."

        lines = [
            "### MEMORA Execution History Timeline",
            "",
            "| Execution ID | Outcome | Tasks Executed | Latency | Caregiver Involved | Timestamp |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in records:
            t_str = r.timestamp_iso[11:16]
            lines.append(
                f"| `{r.execution_id}` | **{r.completion_status.value}** | {len(r.tasks_executed)} | {r.latency_ms:.1f}ms | {'Yes' if r.caregiver_involvement else 'No'} | {t_str} |"
            )

        return "\n".join(lines)
