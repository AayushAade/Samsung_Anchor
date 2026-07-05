import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database SQLite file path
DB_PATH = os.path.join(BASE_DIR, "memora_db.json")

# Face comparison tolerance (standard L2 norm threshold)
FACE_TOLERANCE = 0.6

# Debug flag
DEBUG = True

# Object detection and ledger settings
SPATIAL_CELL_SIZE = 50
YOLO_MODEL_NAME = "yolov8n.pt"
TRACKED_OBJECTS = ["phone", "keys", "wallet", "glasses", "backpack"]

# API key for Gemini LLM binder
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
