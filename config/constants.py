"""
Shared project constants.
"""

# Runtime
APP_NAME = "Samsung Anchor"
APP_VERSION = "0.1.0"

# Vision
DEFAULT_FACE_TOLERANCE = 0.60

# Audio
DEFAULT_AUDIO_DURATION = 5

# Memory
DEFAULT_SPATIAL_CELL_SIZE = 1.0

# Object Detection
DEFAULT_YOLO_MODEL = "yolov8n.pt"

TRACKED_OBJECTS = [
    "person",
    "cell phone",
    "bottle",
    "cup",
    "chair",
    "book",
    "remote",
    "keys",
    "backpack",
    "laptop",
]