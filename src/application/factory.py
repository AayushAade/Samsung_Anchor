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


HARDWARE_MODES = {"LAPTOP", "RASPBERRY_PI", "JETSON", "PRODUCTION"}


def hardware_config_for(live_hardware: Optional[bool]):
    """
    The one place that decides whether real devices may be used.

    Only an explicit live_hardware=True (the --live-hardware flag) selects a hardware
    runtime; MEMORA_PROFILE then chooses which hardware profile. Text chat, simulation
    and the default runtime are always simulated, whatever the environment says.
    """
    from src.runtime.runtime_models import HardwareConfig, RuntimeMode
    if live_hardware is not True:
        return HardwareConfig(mode=RuntimeMode.SIMULATION)
    import os
    requested = os.environ.get("MEMORA_PROFILE", "").upper()
    mode = RuntimeMode[requested] if requested in HARDWARE_MODES else RuntimeMode.LAPTOP
    return HardwareConfig(mode=mode)


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
    # Anything other than an explicit hardware request uses simulated perception and typed input.
    use_mock = live_hardware is not True

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
        hardware_config=hardware_config_for(live_hardware),
    )

    coordinator.initialize()

    return coordinator