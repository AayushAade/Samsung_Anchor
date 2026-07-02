import cv2
import numpy as np
import time

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[Face Recognizer Warning] 'face_recognition' library not available. Face Recognition will run in simulated fallback mode.")

class MemoraFaceRecognizer:
    """
    Identity Anchoring Module (Pillar I).
    Uses OpenCV Haar Cascades for low-power face gating, and face_recognition (dlib)
    for high-accuracy 128D biometric encodings once the face is steadily present.
    """
    def __init__(self, tolerance=0.6, mock_mode=False):
        self.tolerance = tolerance
        self.mock_mode = mock_mode or not FACE_RECOGNITION_AVAILABLE
        
        self.face_cascade = None
        self.face_first_seen_time = None
        self.gating_threshold = 0.5  # 500 milliseconds threshold
        
        if not self.mock_mode:
            try:
                # Load OpenCV Haar Cascade for fast low-power face detection gating
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                print("[Face Recognizer] OpenCV Haar Cascade loaded for face detection gating.")
                print("[Face Recognizer] face_recognition library initialized successfully.")
            except Exception as e:
                print(f"[Face Recognizer Warning] Failed to load Haar Cascade: {e}")

    def process_frame(self, frame, database):
        """
        Processes a BGR camera frame.
        1. Fast gate: Checks face presence using Haar Cascade (low CPU).
        2. Gating filter: Only proceeds to dlib if face is steady for >= 500ms.
        3. Heavy: Computes 128D encodings and matches in SQLite database.
        """
        results = []
        if frame is None:
            return results

        h, w, _ = frame.shape

        if self.mock_mode:
            # Simulated mode
            top, right, bottom, left = h // 4, 3 * w // 4, 3 * h // 4, w // 4
            
            face_region = frame[top:bottom, left:right]
            avg_color = face_region.mean(axis=(0, 1)) if face_region.size > 0 else [128.0, 128.0, 128.0]
            
            mock_embedding = np.zeros(128)
            mock_embedding[0] = avg_color[0] / 255.0
            mock_embedding[1] = avg_color[1] / 255.0
            mock_embedding[2] = avg_color[2] / 255.0
            
            norm = np.linalg.norm(mock_embedding)
            if norm > 0:
                mock_embedding = mock_embedding / norm

            face_id, info, dist = database.find_match(mock_embedding, self.tolerance)
            is_new = False
            if face_id is None:
                face_id = database.register_anonymous(mock_embedding)
                info = database.get_identity(face_id)
                is_new = True

            results.append({
                "box": (top, right, bottom, left),
                "face_id": face_id,
                "name": info["name"],
                "relationship": info["relationship"],
                "is_new": is_new,
                "embedding": mock_embedding
            })
            return results

        # Real detection mode using Haar Cascade gating + face_recognition
        try:
            # 1. Fast, low-power face detection gate
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = []
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            
            if len(faces) == 0:
                # No face detected, reset the gating timer
                self.face_first_seen_time = None
                return results

            # Face is present, verify gating timer
            now = time.time()
            if self.face_first_seen_time is None:
                self.face_first_seen_time = now
                print("[Face Recognizer] Face detected. Calibrating gating filter (500ms)...")
                return results
                
            elapsed = now - self.face_first_seen_time
            if elapsed < self.gating_threshold:
                # Still waiting for the 500ms steady confirmation
                return results

            # 2. Gate passed - Run heavy dlib 128D encoding pipeline
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            if not face_locations:
                return results

            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for box, encoding in zip(face_locations, face_encodings):
                face_id, info, dist = database.find_match(encoding, self.tolerance)
                is_new = False
                
                if face_id is None:
                    face_id = database.register_anonymous(encoding)
                    info = database.get_identity(face_id)
                    is_new = True
                else:
                    if dist > 0.15 and len(info["embeddings"]) < 10:
                        database.add_embedding_to_identity(face_id, encoding)

                results.append({
                    "box": box,
                    "face_id": face_id,
                    "name": info["name"],
                    "relationship": info["relationship"],
                    "is_new": is_new,
                    "embedding": encoding
                })
        except Exception as e:
            print(f"[Face Recognizer Error] face_recognition processing failed: {e}")
            
        return results

    def draw_faces(self, frame, results):
        """Draws bounding boxes and labels on the frame for visualization."""
        if frame is None:
            return
        
        for res in results:
            top, right, bottom, left = res["box"]
            face_id = res["face_id"]
            name = res["name"]
            relationship = res["relationship"]

            is_recognized = name is not None
            color = (0, 255, 0) if is_recognized else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            if is_recognized:
                if relationship:
                    label = f"{name} ({relationship})"
                else:
                    label = name
            else:
                label = f"New Face: {face_id}"

            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
