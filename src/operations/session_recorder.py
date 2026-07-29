"""
MEMORA Demonstration Session Recorder.

Captures real-time operational events, decision timelines, recognition events,
and caregiver observations to produce replayable session artifacts.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any


class SessionRecorder:
    """
    Records operational demonstration sessions into JSON and Markdown artifacts.
    """

    def __init__(self, session_name: str = "Samsung_Demo_Session") -> None:
        self.session_name = session_name
        self.start_time = time.time()
        self.events: list[dict[str, Any]] = []

    def record_event(self, category: str, title: str, details: dict[str, Any] | None = None) -> None:
        """Record an event entry in the current session log."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "relative_sec": round(time.time() - self.start_time, 2),
            "category": category,
            "title": title,
            "details": details or {},
        }
        self.events.append(entry)

    def export_session(self, output_dir: str = "validation/artifacts") -> tuple[str, str]:
        """
        Export recorded session log to JSON and Markdown artifacts.

        Returns
        -------
        tuple[str, str]
            Tuple of (json_filepath, markdown_filepath)
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")

        json_file = os.path.join(output_dir, f"session_{timestamp_str}.json")
        md_file = os.path.join(output_dir, f"session_{timestamp_str}.md")

        session_data = {
            "session_name": self.session_name,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.localtime(self.start_time)),
            "duration_seconds": round(time.time() - self.start_time, 2),
            "event_count": len(self.events),
            "events": self.events,
        }

        with open(json_file, "w") as f:
            json.dump(session_data, f, indent=2)

        # Generate Markdown Replay Log
        lines = [
            f"# MEMORA Demonstration Session Log ({timestamp_str})",
            "",
            f"**Session Name**: {self.session_name}  ",
            f"**Duration**: {session_data['duration_seconds']} seconds  ",
            f"**Recorded Events**: {len(self.events)}  ",
            "",
            "---",
            "",
            "## Event Sequence Log",
            "",
            "| Relative Time (s) | Category | Event Title | Details |",
            "| :--- | :--- | :--- | :--- |",
        ]

        for ev in self.events:
            details_str = json.dumps(ev["details"]) if ev["details"] else "-"
            lines.append(f"| +{ev['relative_sec']}s | **{ev['category']}** | {ev['title']} | `{details_str}` |")

        with open(md_file, "w") as f:
            f.write("\n".join(lines))

        return json_file, md_file
