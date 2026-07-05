import os
import sys
import json
import argparse
import time
import cv2
import numpy as np
from typing import List, Dict, Any

# Ensure parent directory is in path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.vision.detector import FaceDetector
from src.vision.tracker import FaceTracker
from src.vision.recognizer import FaceRecognizer
from src.vision.registration import FaceRegistrar


PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_profiles.json")


def load_known_profiles() -> List[Dict[str, Any]]:
    """Loads registered face profiles from the local JSON file."""
    if not os.path.exists(PROFILES_FILE):
        return []
    try:
        with open(PROFILES_FILE, "r") as f:
            profiles = json.load(f)
            # Ensure embedding is converted back to list of floats if needed
            return profiles
    except Exception as e:
        print(f"[Test Runner Warning] Failed to load profiles: {e}")
        return []


def save_profile_callback(profile: dict) -> None:
    """Saves a newly registered profile to the local JSON file."""
    profiles = load_known_profiles()
    
    # Remove existing profile with the same name if it exists
    profiles = [p for p in profiles if p["name"] != profile["name"]]
    profiles.append(profile)

    try:
        with open(PROFILES_FILE, "w") as f:
            json.dump(profiles, f, indent=4)
        print(f"[Test Runner] Successfully saved profile for {profile['name']} to {PROFILES_FILE}")
    except Exception as e:
        print(f"[Test Runner Error] Failed to save profile: {e}")


def generate_mock_embedding(face_crop: np.ndarray, name_seed: str = None) -> np.ndarray:
    """Generates a deterministic mock normalized 512D embedding for testing without the ONNX model."""
    if name_seed:
        # Use name hash to seed generator for registration testing
        seed_val = sum(ord(c) for c in name_seed)
    else:
        # Use crop pixel mean to seed generator for recognition testing
        seed_val = int(np.mean(face_crop) * 1000) if face_crop is not None else 42
        
    rng = np.random.default_rng(seed_val % (2**32))
    emb = rng.random(512)
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb


def main():
    parser = argparse.ArgumentParser(description="Samsung Anchor - Vision & Identity Test Runner")
    parser.add_argument("--register", type=str, help="Register a new person by name using the webcam")
    parser.add_argument("--mock", action="store_true", help="Use mock embeddings if ONNX model is missing")
    parser.add_argument("--threshold", type=float, default=0.45, help="Cosine similarity matching threshold")
    parser.add_argument("--samples", type=int, default=20, help="Number of samples to capture for registration")
    args = parser.parse_args()

    # 1. Initialize detector
    try:
        detector = FaceDetector(threshold=0.6)
    except Exception as e:
        print(f"[Test Runner Error] Failed to initialize FaceDetector: {e}")
        print("Please ensure assets/models/scrfd_500m_bnkps.onnx exists.")
        sys.exit(1)

    # 2. Initialize recognizer
    try:
        models_dir = os.path.join(settings.BASE_DIR, "assets", "models")
        model_exists = any(os.path.exists(os.path.join(models_dir, f)) for f in ["w600k_r50.onnx", "w600k_mobi.onnx"])
        
        # Instantiate recognizer (it will lazy-load the session if model exists)
        recognizer = FaceRecognizer(threshold=args.threshold)
        
        if args.mock or not model_exists:
            print("[Test Runner Info] ArcFace model not found or mock requested. RUNNING IN MOCK EMBEDDING MODE.")
            mock_mode = True
        else:
            mock_mode = False
    except Exception as e:
        print(f"[Test Runner Error] Failed to initialize FaceRecognizer: {e}")
        sys.exit(1)

    tracker = FaceTracker(max_lost_frames=30)

    # 3. Handle Registration Mode
    if args.register:
        registrar = FaceRegistrar(detector, recognizer, min_crop_size=80)
        
        # Override generate_embedding if mock mode is requested
        if mock_mode:
            # Monkeypatch the recognizer behavior to generate mock embeddings
            class MockRecognizer:
                def generate_embedding(self, crop):
                    return generate_mock_embedding(crop, name_seed=args.register)
            registrar.recognizer = MockRecognizer()

        try:
            profile = registrar.register(
                name=args.register,
                camera_source=0,
                num_samples=args.samples,
                save_callback=save_profile_callback,
                show_preview=True
            )
            print("\nRegistration Completed Successfully!")
            print(f"Profile: Name='{profile['name']}', Samples Used={profile['samples_used']}")
        except Exception as e:
            print(f"\n[Test Runner Error] Registration failed: {e}")
        return

    # 4. Handle Recognition Mode
    known_profiles = load_known_profiles()
    print(f"[Test Runner] Loaded {len(known_profiles)} known profiles from storage.")

    # Start webcam capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Test Runner Error] Could not access physical webcam.")
        sys.exit(1)

    print("Camera Started")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Test Runner Error] Failed to grab frame.")
                break

            # A. Detect faces
            detections = detector.detect(frame)

            # B. Track faces
            tracked_detections = tracker.update(detections)

            # C. Crop and Recognize each face
            for det in tracked_detections:
                bbox = det["bbox"]
                track_id = det["track_id"]

                # Crop face
                face_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]

                # Generate embedding
                if mock_mode:
                    embedding = generate_mock_embedding(face_crop)
                else:
                    embedding = recognizer.generate_embedding(face_crop)

                print("Detected Face")
                
                if embedding is not None:
                    print("Embedding Generated")
                    # D. Database matching / Cosine similarity comparison
                    result = recognizer.match_embedding(embedding, known_profiles)
                    print(f"Identity : {result['identity']}")
                    print(f"Similarity : {result['similarity']:.2f}")
                else:
                    print("Embedding Generation Failed")

            # Draw preview on screen
            preview_frame = frame.copy()
            for det in tracked_detections:
                bbox = det["bbox"]
                track_id = det["track_id"]
                cv2.rectangle(preview_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(
                    preview_frame,
                    f"ID: {track_id}",
                    (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
            
            try:
                cv2.imshow("Memora Live Face Recognition (Press 'q' to Quit)", preview_frame)
            except Exception:
                # Headless environment or display error, skip showing window
                pass

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


if __name__ == "__main__":
    main()
