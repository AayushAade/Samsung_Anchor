import os
import json
import cv2
import numpy as np
from typing import List, Dict, Any, Union
from src.vision.detector import FaceDetector
from src.vision.recognizer import FaceRecognizer

class FaceRegistrar:
    """
    FaceRegistrar class responsible for capturing and registering face samples
    for a given name, averaging their 128D embeddings, and saving them.
    No recognition is performed here.
    """

    def __init__(self, detector: FaceDetector, recognizer: FaceRecognizer):
        """
        Initializes the FaceRegistrar.

        Args:
            detector: An instance of FaceDetector.
            recognizer: An instance of FaceRecognizer.
        """
        self.detector = detector
        self.recognizer = recognizer

    def register(
        self,
        name: str,
        camera_source: int = 0,
        num_samples: int = 20,
    ) -> dict:
        """
        Captures face samples from the camera, generates embeddings, averages them,
        and saves the profile.

        Args:
            name: The name of the person being registered.
            camera_source: Video capture device index (int).
            num_samples: Number of valid samples to collect (default 20).

        Returns:
            A dictionary of the registered profile.
        """
        if not name:
            raise ValueError("A valid name must be provided for registration.")

        cap = cv2.VideoCapture(camera_source)
        if not cap.isOpened():
            raise RuntimeError("Could not open camera source for registration.")

        print("Camera Started")
        print(f"Registering face for: {name}")
        print(f"Collecting {num_samples} samples. Please look at the camera...")

        valid_embeddings = []

        try:
            while len(valid_embeddings) < num_samples:
                ret, frame = cap.read()
                if not ret:
                    continue

                # 1. Detect faces
                detections = self.detector.detect(frame)

                # Collect only if exactly one face is detected to avoid noise
                if len(detections) == 1:
                    det = detections[0]
                    bbox = det["bbox"]
                    conf = det["confidence"]

                    if conf >= self.detector.threshold:
                        # 2. Crop face
                        face_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                        
                        # 3. Generate embedding
                        embedding = self.recognizer.generate_embedding(face_crop)
                        if embedding is not None:
                            valid_embeddings.append(embedding)
                            print(f"Collected: {len(valid_embeddings)}/{num_samples}")

                # Optional: brief sleep to avoid duplicate frames too quickly
                cv2.waitKey(100)
        finally:
            cap.release()

        if not valid_embeddings:
            raise RuntimeError("No valid face samples were collected.")

        # 4. Average all valid embeddings
        avg_embedding = np.mean(valid_embeddings, axis=0)

        # Normalize the averaged embedding
        norm = np.linalg.norm(avg_embedding)
        if norm > 0:
            avg_embedding = avg_embedding / norm

        profile = {
            "name": name,
            "embedding": avg_embedding.tolist(),
            "samples_used": len(valid_embeddings),
        }

        # 5. Save embedding
        self.save_profile(profile)
        return profile

    def save_profile(self, profile: dict) -> None:
        """Saves the profile to the JSON database."""
        db_path = self.recognizer.db_path
        profiles = []
        if os.path.exists(db_path):
            try:
                with open(db_path, "r") as f:
                    profiles = json.load(f)
            except Exception:
                profiles = []

        # Remove any existing profile with the same name
        profiles = [p for p in profiles if p.get("name") != profile["name"]]
        profiles.append(profile)

        with open(db_path, "w") as f:
            json.dump(profiles, f, indent=4)
        print(f"Profile saved successfully for {profile['name']}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Register a new face profile")
    parser.add_argument("--name", type=str, required=True, help="Name of the person")
    parser.add_argument("--samples", type=int, default=20, help="Number of face samples to capture")
    args = parser.parse_args()

    # Suppress onnxruntime and opencv logs/warnings
    os.environ["ORT_LOGGING_LEVEL"] = "3"
    os.environ["OPENCV_LOG_LEVEL"] = "OFF"

    detector = FaceDetector()
    recognizer = FaceRecognizer()
    registrar = FaceRegistrar(detector, recognizer)
    try:
        registrar.register(name=args.name, num_samples=args.samples)
    except Exception as e:
        print(f"Registration failed: {e}")
