"""
MEMORA Cognitive I/O Explainer.

Generates deterministic Markdown summaries of external input messages, outbound outputs,
routing decisions, session correlations, and rejected message diagnostics.
"""

from __future__ import annotations

from typing import List

from src.io.io_engine import IOEngine


class IOExplainer:
    """
    Deterministic Markdown narrative generator for cognitive I/O boundary reports.
    """

    @classmethod
    def explain_io_state(cls, engine: IOEngine) -> str:
        snap = engine.snapshot()
        rec_messages = engine.input_gateway.get_received_messages()
        sent_messages = engine.output_gateway.get_sent_messages()
        routed_decisions = engine.router.get_routed_decisions()

        lines = [
            "# MEMORA Unified Cognitive I/O Diagnostic Report",
            "",
            "## Executive Summary",
            f"- **Ingress Received Messages**: {snap.received_messages_count}",
            f"- **Egress Prepared Outputs**: {snap.sent_messages_count}",
            f"- **Routed Message Decisions**: {snap.routed_messages_count}",
            f"- **Rejected / Failed Messages**: {snap.rejected_messages_count}",
            f"- **I/O Traffic Checksum (SHA256)**: `{snap.checksum}`",
            "",
            "## Ingress Message Summary",
        ]

        if rec_messages:
            for msg in rec_messages:
                in_type_str = msg.input_type.value if msg.input_type else "UNKNOWN"
                ses_str = f" [Session: `{msg.session_id}`]" if msg.session_id else ""
                lines.append(
                    f"- **`{msg.message_id}`** ({msg.source} → {msg.destination}) Type: `{in_type_str}` PayloadRef: `{msg.payload_reference}`{ses_str}"
                )
        else:
            lines.append("• No external ingress messages received.")

        lines.append("")
        lines.append("## Egress Message Summary")
        if sent_messages:
            for msg in sent_messages:
                out_type_str = msg.output_type.value if msg.output_type else "UNKNOWN"
                ses_str = f" [Session: `{msg.session_id}`]" if msg.session_id else ""
                lines.append(
                    f"- **`{msg.message_id}`** ({msg.source} → {msg.destination}) Type: `{out_type_str}` PayloadRef: `{msg.payload_reference}`{ses_str}"
                )
        else:
            lines.append("• No outbound egress messages generated.")

        lines.append("")
        lines.append("## Routing Decisions Breakdown")
        for dec in routed_decisions:
            status_str = "ACCEPTED" if dec.accepted else "REJECTED"
            lines.append(
                f"- Destination: `{dec.destination}` [{status_str}] Rationale: {dec.reason}"
            )

        lines.append("")
        lines.append("## Recommended Actions")
        if snap.rejected_messages_count > 0:
            lines.append("• Audit rejected message schemas and session ID parameters.")
        lines.append("• Ensure future hardware adapters (Camera, Audio, BLE) route strictly through InputGateway.")

        return "\n".join(lines)
