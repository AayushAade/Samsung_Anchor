"""
MEMORA Edge Runtime & Device Integration Explainer.

Generates deterministic Markdown reports synthesizing registered device profiles, active
deployment capability matrices, resource policy evaluations, and runtime warnings.
"""

from __future__ import annotations

from typing import List

from src.edge.edge_engine import EdgeEngine


class EdgeExplainer:
    """
    Deterministic Markdown narrative generator for edge runtime diagnostics.
    Synthesizes hardware profile configurations and active capability availability
    without generative AI text models or platform SDK calls.
    """

    @classmethod
    def explain_engine_state(cls, engine: EdgeEngine) -> str:
        """
        Generate a comprehensive, deterministic Markdown diagnostic report of current edge runtime state,
        registered hardware profiles, active capabilities, and evaluated resource policies.
        """
        snap = engine.snapshot()
        devices = engine.registry.list_devices()
        active_caps = engine.capability_manager.get_active_capabilities()
        warnings = engine.runtime_monitor.get_warnings()
        policies = engine.resource_manager.get_policy_history()

        lines = [
            "# MEMORA Edge Runtime & Device Integration Diagnostic Report",
            "",
            "## Executive Summary",
            f"- **Active Deployment Profile**: `{snap.active_profile_name}`",
            f"- **Current Runtime Health State**: `{snap.current_runtime_state.value}`",
            f"- **Registered Device Profiles**: {snap.registered_devices_count}",
            f"- **Active Abstract Capabilities**: {snap.available_capabilities_count}",
            f"- **Edge Framework Checksum (SHA256)**: `{snap.checksum}`",
            "",
            "## Registered Devices Overview",
        ]

        if devices:
            for dev in devices:
                lines.append(
                    f"- **`{dev.device_id}`** ({dev.device_type.value}) — "
                    f"Battery: {dev.battery_level:.1f}% | Storage: {dev.available_storage:.1f} MB"
                )
        else:
            lines.append("• No edge devices registered.")

        lines.append("")
        lines.append("## Active Capability Matrix")
        for cap in active_caps:
            essential_flag = " [ESSENTIAL]" if cap.is_essential() else ""
            lines.append(f"- • `{cap.value}`: ACTIVE & AVAILABLE{essential_flag}")

        lines.append("")
        lines.append("## Runtime Health Warnings & Resource Policies")
        if warnings:
            for w in warnings:
                lines.append(f"⚠️ {w}")
        else:
            lines.append("✅ Runtime health operating within normal baseline parameters.")

        if policies and policies[-1][2]:
            lines.append("")
            lines.append("### Evaluated Resource Policies")
            for pol in policies[-1][2]:
                lines.append(f"- • {pol}")

        lines.append("")
        lines.append("## Heterogeneous Form-Factor Support Matrix")
        lines.append("• **Smartphone**: Full capability profile (Camera, Mic, Speaker, Display, Storage, Network, GPS).")
        lines.append("• **Smartwatch**: Haptic and audio-focused profile (Mic, Speaker, Haptic, Small Display, Storage).")
        lines.append("• **Smart Glasses**: Vision-first wearable profile (Camera, Mic, Speaker, HUD Display, Storage).")
        lines.append("• **Offline Clinical Device**: Network-independent profile (Camera, Mic, Speaker, Display, Local Storage).")

        lines.append("")
        lines.append("## Architectural Portability & Offline Assurance")
        lines.append("• Zero operating-system SDK, Bluetooth, or platform driver dependencies.")
        lines.append("• Hardware-independent abstractions enable seamless deployment across Phone, Watch, and Glasses.")
        lines.append("• Offline-first design guarantees cognitive execution when network is unavailable.")

        return "\n".join(lines)
