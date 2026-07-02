import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project directory paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database Path
DB_PATH = os.getenv("MEMORA_DB_PATH", str(BASE_DIR / "memora_db.json"))

# Face Recognition Settings
# A tolerance of 0.6 is standard for dlib. Lower values are stricter.
FACE_TOLERANCE = float(os.getenv("FACE_TOLERANCE", "0.6"))

# Audio Recording Settings
AUDIO_DURATION_SEC = int(os.getenv("AUDIO_DURATION_SEC", "5"))
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))

# YOLO Object Tracking Settings
YOLO_MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolov8n.pt")
# High-value daily objects we want to passively track in the spatial ledger
TRACKED_OBJECTS = [
    "cell phone", "keys", "glasses", "backpack", "wallet", 
    "remote", "book", "cup", "bottle", "handbag", "umbrella"
]
SPATIAL_CELL_SIZE = int(os.getenv("SPATIAL_CELL_SIZE", "100"))

