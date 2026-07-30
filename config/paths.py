"""
Project paths.

Defines filesystem locations used throughout Samsung Anchor.
"""

from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Assets
ASSETS_DIR = BASE_DIR / "assets"

# Data
DATA_DIR = BASE_DIR / "data"

# Database
DATABASE_PATH = BASE_DIR / "memora_db.sqlite"

# Models
YOLO_MODEL_PATH = BASE_DIR / "yolov8n.pt"
SCRFD_MODEL_PATH = ASSETS_DIR / "scrfd_500m_bnkps.onnx"