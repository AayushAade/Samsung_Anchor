import cv2
import numpy as np
import time
from config import settings

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[Object Ledger Warning] 'ultralytics' library not available. Object tracking will run in simulated fallback mode.")

class SpatialHashMap:
    """
    A 2D Spatial Hash Map for indexing objects by their screen coordinates.
    Divides the frame space into fixed-size grid cells.
    """
    def __init__(self, cell_size=None):
        self.cell_size = cell_size or settings.SPATIAL_CELL_SIZE
        self.grid = {}  # (cell_x, cell_y) -> list of objects

    def hash_point(self, x, y):
        """Hashes an (x, y) coordinate to a grid cell coordinate."""
        return int(x // self.cell_size), int(y // self.cell_size)

    def insert(self, name, x, y, data=None):
        """Inserts an object location into the spatial hash map."""
        cell = self.hash_point(x, y)
        if cell not in self.grid:
            self.grid[cell] = []
        self.grid[cell].append({
            "name": name,
            "coords": (float(x), float(y)),
            "data": data,
            "timestamp": time.time()
        })

    def get_items_in_cell(self, x, y):
        """Retrieves all objects located in the same cell as the given point."""
        cell = self.hash_point(x, y)
        return self.grid.get(cell, [])

    def get_grid_quadrant(self, x, y, width=640, height=480):
        """
        Translates raw (x, y) coordinates into a human-readable screen section.
        Useful for natural language direction generation.
        """
        x_pct = x / width if width > 0 else 0.5
        y_pct = y / height if height > 0 else 0.5

        h_desc = "left" if x_pct < 0.35 else ("right" if x_pct > 0.65 else "middle")
        v_desc = "top" if y_pct < 0.35 else ("bottom" if y_pct > 0.65 else "center")

        if h_desc == "middle" and v_desc == "center":
            return "center area"
        return f"{v_desc}-{h_desc} area"

    def clear(self):
        """Clears all grid mappings."""
        self.grid.clear()


class MemoraObjectTracker:
    """
    YOLOv8-based passive object tracker (Pillar II).
    Detects and logs coordinates of tracked objects in a spatial grid.
    """
    def __init__(self, mock_mode=False):
        self.mock_mode = mock_mode or not YOLO_AVAILABLE
        self.tracked_objects = settings.TRACKED_OBJECTS
        self.spatial_hash = SpatialHashMap()
        self.model = None

        if not self.mock_mode:
            try:
                # Load the pre-trained YOLOv8-nano model (lightweight for edge/local usage)
                self.model = YOLO(settings.YOLO_MODEL_NAME)
                print(f"[Object Ledger] YOLOv8 model loaded: {settings.YOLO_MODEL_NAME}")
            except Exception as e:
                print(f"[Object Ledger Warning] Failed to load YOLO model: {e}. Enabling mock fallback.")
                self.mock_mode = True

        # Mock simulation state
        self.mock_detections = [
            {"name": "cell phone", "box": (120, 180, 260, 320), "confidence": 0.88, "seen_interval": (0, 12)},
            {"name": "keys", "box": (400, 120, 480, 200), "confidence": 0.91, "seen_interval": (5, 20)},
            {"name": "glasses", "box": (280, 300, 360, 410), "confidence": 0.85, "seen_interval": (10, 25)}
        ]

    def detect_objects(self, frame):
        """
        Runs object detection on a frame.
        Returns:
            list: [ { "name": str, "box": (x1, y1, x2, y2), "confidence": float, "center": (cx, cy) } ]
        """
        results = []
        if frame is None:
            return results

        h, w, _ = frame.shape
        self.spatial_hash.clear()

        if self.mock_mode:
            # Simulate object presence based on standard cycle times
            current_sec = int(time.time()) % 30
            for item in self.mock_detections:
                start, end = item["seen_interval"]
                if start <= current_sec <= end:
                    x1, y1, x2, y2 = item["box"]
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    
                    # Store in spatial hash map
                    self.spatial_hash.insert(item["name"], cx, cy, {"confidence": item["confidence"]})
                    
                    results.append({
                        "name": item["name"],
                        "box": (x1, y1, x2, y2),
                        "confidence": item["confidence"],
                        "center": (cx, cy)
                    })
            return results

        # Real YOLOv8 inference
        try:
            # Run YOLO on the BGR frame directly
            outputs = self.model(frame, verbose=False)
            if outputs and len(outputs) > 0:
                boxes = outputs[0].boxes
                for box in boxes:
                    # Get class name
                    cls_idx = int(box.cls[0].item())
                    cls_name = self.model.names[cls_idx]
                    
                    # Filter only the high-value items we want to track
                    if cls_name in self.tracked_objects:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = box.conf[0].item()
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2

                        # Store in spatial hash map
                        self.spatial_hash.insert(cls_name, cx, cy, {"confidence": conf})

                        results.append({
                            "name": cls_name,
                            "box": (int(x1), int(y1), int(x2), int(y2)),
                            "confidence": conf,
                            "center": (cx, cy)
                        })
        except Exception as e:
            print(f"[Object Ledger Error] YOLO inference failed: {e}")

        return results

    def draw_ledger_overlay(self, frame, detections):
        """
        Draws the spatial hash map grid overlay and bounding boxes on the frame.
        """
        if frame is None:
            return

        h, w, _ = frame.shape
        cell_size = self.spatial_hash.cell_size

        # 1. Draw Spatial Hash Map grid lines (subtle cyan/gray overlay)
        grid_color = (80, 80, 80)
        grid_thickness = 1
        
        # Vertical grid lines
        for x in range(0, w, cell_size):
            cv2.line(frame, (x, 0), (x, h), grid_color, grid_thickness)
            # Add grid labels
            cv2.putText(frame, f"x:{x//cell_size}", (x + 5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.3, grid_color, 1)

        # Horizontal grid lines
        for y in range(0, h, cell_size):
            cv2.line(frame, (0, y), (w, y), grid_color, grid_thickness)
            cv2.putText(frame, f"y:{y//cell_size}", (5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, grid_color, 1)

        # 2. Draw object bounding boxes and spatial label
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            name = det["name"]
            conf = det["confidence"]
            cx, cy = det["center"]

            # Compute quadrant/section label
            quadrant = self.spatial_hash.get_grid_quadrant(cx, cy, w, h)
            label = f"{name} ({conf:.2f}) - {quadrant}"

            # Box outline (Cyan for high-tech HUD feel)
            color = (255, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Center pointer
            cv2.circle(frame, (int(cx), int(cy)), 4, color, -1)

            # Label banner
            cv2.rectangle(frame, (x1, y1 - 25), (x2, y1), color, cv2.FILLED)
            cv2.putText(
                frame, 
                label, 
                (x1 + 5, y1 - 7), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.45, 
                (0, 0, 0), 
                1, 
                cv2.LINE_AA
            )
