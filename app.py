"""
Samsung Anchor Application

Official application entry point.

This module is responsible for assembling the application's
major subsystems and constructing the AnchorCoordinator.

Business logic does NOT belong here.
"""

from __future__ import annotations

from typing import Any

from src.coordinator.anchor_coordinator import AnchorCoordinator


def build_application(
    database: Any,
    recognizer: Any,
    listener: Any,
    binder: Any,
    speaker: Any,
) -> AnchorCoordinator:
    """
    Build and return the application's coordinator.

    All subsystem instances are injected into the coordinator.
    """

    return AnchorCoordinator(
        database=database,
        recognizer=recognizer,
        listener=listener,
        binder=binder,
        speaker=speaker,
    )


def main() -> None:
    """
    Application entry point.

    The real subsystem construction will be added in a future sprint.
    """

    print("Samsung Anchor")
    print("Application bootstrap initialized.")


if __name__ == "__main__":
    main()