import os
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import sys
import logging
logging.getLogger("onnxruntime").setLevel(logging.ERROR)

import cv2
import warnings
warnings.filterwarnings("ignore")

from src.vision.detector import FaceDetector
from src.vision.recognizer import FaceRecognizer
from src.vision.tracker import FaceTracker

def main():
    # Initialize detector, recognizer, and tracker
    try:
        detector = FaceDetector()
        recognizer = FaceRecognizer()
        tracker = FaceTracker()
    except Exception as e:
        # Silently exit or print minimal info if initialization fails
        sys.exit(1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit(1)

    print("Camera Started")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            detections = detector.detect(frame)
            if detections:
                # Update tracker to keep track IDs stable
                tracked_detections = tracker.update(detections)

                for det in tracked_detections:
                    bbox = det["bbox"]
                    # Crop face from BGR frame
                    face_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                    
                    print("Detected Face")
                    
                    # Generate embedding and recognize
                    identity, distance = recognizer.recognize(face_crop)
                    print("Embedding Generated")
                    print(f"Identity : {identity}")
                    print(f"Distance : {distance:.2f}")

            # Exit key check
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

if __name__ == "__main__":
    main()
