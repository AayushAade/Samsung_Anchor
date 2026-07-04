import sys
from config import settings

def log_event(event_type, message):
    """
    Centralized event logger for Memora.
    Formats and prints system-wide events.
    """
    prefix = ""
    if event_type == "face_enter":
        prefix = "👤 [Face Action]"
    elif event_type == "face_leave":
        prefix = "👤 [Face Action]"
    elif event_type == "cand_create":
        prefix = "🔍 [Tracking]"
    elif event_type == "cand_promote":
        prefix = "🚀 [Identity]"
    elif event_type == "recognized":
        prefix = "✅ [Identity]"
    elif event_type == "confirmed":
        prefix = "👑 [Identity]"
    elif event_type == "audio_start":
        prefix = "🎙️ [Audio]"
    elif event_type == "transcript":
        prefix = "📝 [Audio]"
    elif event_type == "evidence":
        prefix = "📊 [Evidence]"
    elif event_type == "speaker":
        prefix = "🔊 [Speaker]"
    else:
        prefix = "ℹ️ [System]"

    print(f"{prefix} {message}")
    sys.stdout.flush()
