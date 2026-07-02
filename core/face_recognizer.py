import cv2
import numpy as np

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[Face Recognizer Warning] 'face_recognition' library not available. Face Recognition will run in simulated fallback mode.")

class MemoraFaceRecognizer:
    """
    Identity Anchoring Module (Pillar I).
    Uses the face_recognition library (dlib wrapper) to detect faces and compute
    accurate, rotation- and translation-invariant 128-dimensional biometric embeddings.
    Includes a complete mock mode fallback for testing and headless environments.
    """
    def __init__(self, tolerance=0.6, mock_mode=False):
        self.tolerance = tolerance
        self.mock_mode = mock_mode or not FACE_RECOGNITION_AVAILABLE
        if not self.mock_mode:
            print("[Face Recognizer] face_recognition library initialized successfully.")

    def process_frame(self, frame, database):
        """
        Processes a BGR camera frame.
        1. Detects faces using face_recognition
        2. Computes 128D biometric encodings
        3. Queries database to match
        4. If no match, registers as a new Anonymous_ID
        Returns a list of dicts: [ { "box": (top, right, bottom, left), "face_id": str, "name": str/None, "relationship": str/None, "is_new": bool, "embedding": np.ndarray } ]
        """
        results = []
        if frame is None:
            return results

        h, w, _ = frame.shape

        if self.mock_mode:
            # Simulated mode for headless environments / testing
            top, right, bottom, left = h // 4, 3 * w // 4, 3 * h // 4, w // 4
            
            # Construct a deterministic mock embedding based on average color of the face region
            face_region = frame[top:bottom, left:right]
            avg_color = face_region.mean(axis=(0, 1)) if face_region.size > 0 else [128.0, 128.0, 128.0]
            
            mock_embedding = np.zeros(128)
            mock_embedding[0] = avg_color[0] / 255.0
            mock_embedding[1] = avg_color[1] / 255.0
            mock_embedding[2] = avg_color[2] / 255.0
            
            # Unit normalize mock embedding
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

        # Real detection mode using face_recognition
        try:
            # Convert frame from BGR (OpenCV format) to RGB (face_recognition expects RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 1. Detect face locations
            face_locations = face_recognition.face_locations(rgb_frame)
            if not face_locations:
                return results

            # 2. Extract 128D encodings
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for box, encoding in zip(face_locations, face_encodings):
                # 3. Search in database
                face_id, info, dist = database.find_match(encoding, self.tolerance)
                is_new = False
                
                if face_id is None:
                    # Register new anonymous person
                    face_id = database.register_anonymous(encoding)
                    info = database.get_identity(face_id)
                    is_new = True
                else:
                    # Reinforce identity by adding embedding if it is slightly different
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

            # Set colors (green for recognized, red for anonymous/new)
            is_recognized = name is not None
            color = (0, 255, 0) if is_recognized else (0, 0, 255)

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Construct label
            if is_recognized:
                if relationship:
                    label = f"{name} ({relationship})"
                else:
                    label = name
            else:
                label = f"New Face: {face_id}"

            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
