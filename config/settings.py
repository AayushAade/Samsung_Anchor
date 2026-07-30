"""
Global runtime configuration for Samsung Anchor.
"""

from __future__ import annotations

import os

# Prevent OpenMP duplicate runtime library crashes across PyTorch, OpenCV, and FAISS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

from config.constants import (
    DEFAULT_AUDIO_DURATION,
    DEFAULT_FACE_TOLERANCE,
    DEFAULT_SPATIAL_CELL_SIZE,
    DEFAULT_YOLO_MODEL,
    TRACKED_OBJECTS as DEFAULT_TRACKED_OBJECTS,
)
from config.paths import (
    BASE_DIR,
    DATABASE_PATH,
)

# ==========================================================
# General
# ==========================================================

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1")

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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ==========================================================
# Object Memory
# ==========================================================

YOLO_MODEL_NAME = DEFAULT_YOLO_MODEL

SPATIAL_CELL_SIZE = DEFAULT_SPATIAL_CELL_SIZE

TRACKED_OBJECTS = DEFAULT_TRACKED_OBJECTS
