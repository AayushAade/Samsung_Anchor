"""
Application Factory

This module assembles the Samsung Anchor application by wiring together
the application's major subsystems.

The factory is responsible only for construction.

It does NOT contain business logic.
It does NOT execute the application.
It does NOT process frames or transcripts.
"""

from __future__ import annotations

from typing import Any

from src.coordinator.anchor_coordinator import AnchorCoordinator
from src.memory.database import MemoraDatabase
from src.vision.face_recognizer import MemoraFaceRecognizer
from src.audio.audio_listener import MemoraAudioListener
from src.reasoning.context_binder import MemoraContextBinder


def build_application(
    *,
    database: MemoraDatabase,
    recognizer: MemoraFaceRecognizer,
    listener: MemoraAudioListener,
    binder: MemoraContextBinder,
    speaker: Any,
) -> AnchorCoordinator:
    """
    Build a Samsung Anchor application.

    Parameters
    ----------
    database
        Memory subsystem.

    recognizer
        Vision subsystem.

    listener
        Audio subsystem.

    binder
        Reasoning subsystem.

    speaker
        Speech output subsystem.

    Returns
    -------
    AnchorCoordinator
        Fully assembled coordinator.
    """

    coordinator = AnchorCoordinator(
        database=database,
        recognizer=recognizer,
        listener=listener,
        binder=binder,
        speaker=speaker,
    )

    coordinator.initialize()

    return coordinator