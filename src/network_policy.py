"""
Outbound network policy.

MEMORA's text chat, simulation and default runtime work fully offline. Every
feature that can contact the internet is off unless its opt-in variable is set
to "1". This module is the single source of truth for those switches and for
what MEMORA tells people about network use.

| Variable                      | Enables                                               | Data sent |
| MEMORA_ALLOW_MODEL_DOWNLOAD=1 | downloading the faster-whisper speech model           | none (model request only) |
| MEMORA_ALLOW_CLOUD_ASR=1      | Google web speech transcription (+ voice consent)     | recorded audio |
| MEMORA_ALLOW_CLOUD_LLM=1      | Gemini name extraction during identity learning (+ GEMINI_API_KEY, + face and memory consent) | introduction transcript |
"""

from __future__ import annotations

import os


def _enabled(name: str) -> bool:
    return os.environ.get(name) == "1"


def model_download_allowed() -> bool:
    return _enabled("MEMORA_ALLOW_MODEL_DOWNLOAD")


def cloud_asr_allowed() -> bool:
    return _enabled("MEMORA_ALLOW_CLOUD_ASR")


def cloud_llm_allowed() -> bool:
    return _enabled("MEMORA_ALLOW_CLOUD_LLM") and bool(os.environ.get("GEMINI_API_KEY"))


def describe() -> list[str]:
    """Plain-language description of what could leave this computer right now."""
    lines = []
    if cloud_llm_allowed():
        lines.append("Gemini (Google) receives introduction transcripts during face-based identity learning.")
    if cloud_asr_allowed():
        lines.append("Google speech recognition receives microphone recordings during identity learning.")
    if model_download_allowed():
        lines.append("The speech-recognition model may be downloaded from huggingface.co (no personal data).")
    return lines or ["Nothing: no network features are enabled."]
