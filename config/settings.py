"""
Global runtime configuration for Samsung Anchor.
"""

from __future__ import annotations

import os

from config.constants import (
    DEFAULT_AUDIO_DURATION,
    DEFAULT_FACE_TOLERANCE,
    DEFAULT_SPATIAL_CELL_SIZE,
    DEFAULT_YOLO_MODEL,
    TRACKED_OBJECTS,
)
from config.paths import (
    BASE_DIR,
    DATABASE_PATH,
)

# ==========================================================
# General
# ==========================================================

DEBUG = True

# ==========================================================
# Database
# ==========================================================

DB_PATH = str(DATABASE_PATH)

# ==========================================================
# Vision
# ==========================================================

FACE_TOLERANCE = DEFAULT_FACE_TOLERANCE

# ==========================================================
# Audio
# ==========================================================

AUDIO_DURATION_SEC = DEFAULT_AUDIO_DURATION

# ==========================================================
# Reasoning
# ==========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================================
# Object Memory
# ==========================================================

YOLO_MODEL_NAME = DEFAULT_YOLO_MODEL

SPATIAL_CELL_SIZE = DEFAULT_SPATIAL_CELL_SIZE

TRACKED_OBJECTS = TRACKED_OBJECTS