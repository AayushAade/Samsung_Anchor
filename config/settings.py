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

# MEMORA_DB_PATH lets operators (and the test suite) point MEMORA at a
# database other than the repository-root default.
DB_PATH = os.environ.get("MEMORA_DB_PATH") or str(DATABASE_PATH)

# Log files can contain what the person said; MEMORA_LOG_DIR relocates them.
LOG_DIR = os.environ.get("MEMORA_LOG_DIR") or os.path.join(str(BASE_DIR), "data", "logs")

# ==========================================================
# Vision
# ==========================================================

FACE_TOLERANCE = DEFAULT_FACE_TOLERANCE
# OpenCV YuNet + SFace backend (src/vision/face_models.py). SFace features are L2-normalised;
# OpenCV's published LFW threshold is L2 1.128 (cosine 0.363). MEMORA uses a stricter value
# because naming the wrong person is worse than not recognising someone. Not yet calibrated
# on real cameras (docs/HARDWARE_TEST_CHECKLIST.md).
SFACE_MATCH_TOLERANCE = 1.0
SFACE_AMBIGUITY_MARGIN = 0.08   # a second identity this close to the best one -> "not sure"
FACE_DETECTION_MIN_SCORE = 0.8  # YuNet score below this is ignored
FACE_MIN_SIZE_PX = 60           # smaller faces are ignored (too little detail to identify)

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
