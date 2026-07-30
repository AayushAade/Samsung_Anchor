"""
MEMORA Session Explainer.

Generates human-readable Markdown summaries for completed CognitiveSessions.
Reuses the session's own execution trace and subsystem participation records
rather than duplicating explainability logic from other subsystems.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.session.session_models import CognitiveSession


class SessionExplainer:
    """
    Produces concise, caregiver-readable session summaries.
    """

    @classmethod
    def explain(cls, session: CognitiveSession) -> str:
        lines = [
            f"### Cognitive Session Summary",
            f"- **Session ID**: `{session.session_id}`",
            f"- **Patient**: {session.patient_id}",
            f"- **Goal**: {session.goal or 'Reactive assistance'}",
            f"- **State**: {session.current_state.value}",
            f"- **Created**: {session.created_at}",
            f"- **Updated**: {session.updated_at}",
            "",
            f"**Participating Subsystems** ({len(session.participating_subsystems)}):",
        ]
        for sub in session.participating_subsystems:
            lines.append(f"  • {sub}")

        lines.append("")
        lines.append(f"**Execution Trace** ({len(session.execution_trace)} steps):")
        for i, step in enumerate(session.execution_trace, 1):
            sub = step.get("subsystem", "?")
            op = step.get("operation", "?")
            dur = step.get("duration_ms", 0.0)
            st = step.get("status", "OK")
            lines.append(f"  {i}. **{sub}** → {op} ({dur:.2f}ms) [{st}]")

        if session.final_result:
            lines.append("")
            lines.append("**Final Result**:")
            action = session.final_result.get("action", "")
            if action:
                lines.append(f"  → {action}")
            error = session.final_result.get("error")
            if error:
                lines.append(f"  ⚠ Error: {error}")

        return "\n".join(lines)
