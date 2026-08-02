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

from typing import Any, Optional

from devices.speaker import SpeakerDevice
from src.coordinator.anchor_coordinator import AnchorCoordinator
from src.memory.database import MemoraDatabase
from src.vision.face_recognizer import MemoraFaceRecognizer
from src.audio.audio_listener import MemoraAudioListener
from src.reasoning.context_binder import MemoraContextBinder


def build_application(
    *,
    live_hardware: Optional[bool] = None,
    database: Optional[MemoraDatabase] = None,
    recognizer: Optional[MemoraFaceRecognizer] = None,
    listener: Optional[MemoraAudioListener] = None,
    binder: Optional[MemoraContextBinder] = None,
    speaker: Optional[Any] = None,
) -> AnchorCoordinator:
    """
    Build a Samsung Anchor application.
    """

    # If live_hardware is None or True, attempt live hardware with simulation fallbacks
    use_mock = (live_hardware is False)

    db = database if database is not None else MemoraDatabase()
    rec = recognizer if recognizer is not None else MemoraFaceRecognizer(mock_mode=use_mock)
    listn = listener if listener is not None else MemoraAudioListener(mock_mode=use_mock)
    bind = binder if binder is not None else MemoraContextBinder()
    spk = speaker if speaker is not None else SpeakerDevice()

    coordinator = AnchorCoordinator(
        database=db,
        recognizer=rec,
        listener=listn,
        binder=bind,
        speaker=spk,
    )

    coordinator.initialize()

    return coordinator