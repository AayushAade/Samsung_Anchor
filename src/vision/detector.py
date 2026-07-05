import os
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
import logging
logging.getLogger("onnxruntime").setLevel(logging.ERROR)

import cv2
import numpy as np
from typing import List, Dict, Any
from config import settings

try:
    from insightface.model_zoo.scrfd import SCRFD
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False


class FaceDetector:
    """
    FaceDetector class responsible for detecting faces using the InsightFace SCRFD model.
    It returns only bounding boxes, landmarks, and confidence scores.
    """

    def __init__(self, model_path: str = None, threshold: float = 0.6):
        """
        Initializes the FaceDetector.

        Args:
            model_path: Path to the SCRFD ONNX model file. If None, it defaults to the
                       path defined in settings.
            threshold: Confidence threshold for face detection. Detections below this
                       value will be filtered out.
        """
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError(
                "InsightFace is not installed or available in this environment."
            )

        if model_path is None:
            model_path = os.path.join(
                settings.BASE_DIR, "assets", "models", "scrfd_500m_bnkps.onnx"
            )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"SCRFD model file not found at: {model_path}. Please place the "
                "scrfd_500m_bnkps.onnx model file in assets/models/."
            )

        self.threshold = threshold
        try:
            self.detector = SCRFD(model_file=model_path)
            # ctx_id=-1 uses CPU for inference, ctx_id=0 uses GPU if available
            self.detector.prepare(ctx_id=-1)
            # Set the detection threshold attribute on the detector object
            self.detector.det_thresh = self.threshold
        except Exception as e:
            raise RuntimeError(f"Failed to load/initialize SCRFD model: {e}")

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects faces in the given BGR frame.

        Args:
            frame: Input image in OpenCV BGR format.

        Returns:
            A list of dictionaries containing:
            - 'bbox': [x1, y1, x2, y2] clipped to frame boundaries.
            - 'landmarks': A list of landmark points.
            - 'confidence': The confidence score (float).
        """
        if frame is None:
            return []

        h, w = frame.shape[:2]
        
        try:
            # Run SCRFD detection
            bboxes, kpss = self.detector.detect(frame)
        except Exception as e:
            # Handle potential model runtime failures gracefully
            print(f"[FaceDetector Error] Model inference failed: {e}")
            return []

        results = []
        if bboxes is not None:
            for i in range(len(bboxes)):
                bbox = bboxes[i]
                x1, y1, x2, y2, score = bbox
                
                # Filter out detections below the threshold (double security)
                if score < self.threshold:
                    continue

                # Clip bounding boxes to image boundaries
                x1_clipped = max(0, min(int(x1), w - 1))
                y1_clipped = max(0, min(int(y1), h - 1))
                x2_clipped = max(0, min(int(x2), w - 1))
                y2_clipped = max(0, min(int(y2), h - 1))

                # Extract landmarks if they exist
                landmarks_list = []
                if kpss is not None and i < len(kpss):
                    kps = kpss[i]
                    landmarks_list = kps.tolist()

                results.append({
                    "bbox": [x1_clipped, y1_clipped, x2_clipped, y2_clipped],
                    "landmarks": landmarks_list,
                    "confidence": float(score)
                })

        return results
