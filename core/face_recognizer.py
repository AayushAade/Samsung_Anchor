import cv2
import numpy as np

try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("[Face Recognizer Warning] 'face_recognition' library not available. Face Recognition will run in simulated fallback mode.")

class MemoraFaceRecognizer:
    def __init__(self, tolerance=0.6, mock_mode=False):
        self.tolerance = tolerance
        self.mock_mode = mock_mode or not FACE_REC_AVAILABLE

    def process_frame(self, frame, database):
        """
        Processes a BGR camera frame.
        1. Detects faces
        2. Computes embeddings
        3. Queries database to match
        4. If no match, registers as a new Anonymous_ID
        Returns a list of dicts: [ { "box": (top, right, bottom, left), "face_id": str, "name": str/None, "relationship": str/None, "is_new": bool } ]
        """
        results = []
        if frame is None:
            return results

        if self.mock_mode:
            # Simulated mode for headless environments / testing
            # We will simulate detecting a face in the center of the screen
            h, w, _ = frame.shape
            # Mock a face bounding box in the middle of the screen
            top, right, bottom, left = h // 4, 3 * w // 4, 3 * h // 4, w // 4
            
            # Use a dummy embedding (128 floats)
            # To simulate different people, we can average the color of the mock face region to make it semi-deterministic
            face_region = frame[top:bottom, left:right]
            avg_color = face_region.mean(axis=(0, 1)) if face_region.size > 0 else [128.0, 128.0, 128.0]
            
            # Construct a deterministic mock embedding based on average color
            mock_embedding = np.zeros(128)
            mock_embedding[0] = avg_color[0] / 255.0
            mock_embedding[1] = avg_color[1] / 255.0
            mock_embedding[2] = avg_color[2] / 255.0
            
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

        # Real detection mode using face_recognition (dlib)
        try:
            # Convert frame from BGR (OpenCV format) to RGB (face_recognition format)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect face locations
            face_locations = face_recognition.face_locations(rgb_frame)
            if not face_locations:
                return results

            # Compute 128D embeddings
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for location, encoding in zip(face_locations, face_encodings):
                # Search in database
                face_id, info, dist = database.find_match(encoding, self.tolerance)
                is_new = False
                
                if face_id is None:
                    # Register new anonymous person
                    face_id = database.register_anonymous(encoding)
                    info = database.get_identity(face_id)
                    is_new = True
                else:
                    # Reinforce identity (optionally add the embedding to the database to capture visual variance)
                    # We only add if the distance is solid but not exact, keeping database size reasonable
                    if dist > 0.1 and len(info["embeddings"]) < 10:
                        database.add_embedding_to_identity(face_id, encoding)

                results.append({
                    "box": location,
                    "face_id": face_id,
                    "name": info["name"],
                    "relationship": info["relationship"],
                    "is_new": is_new,
                    "embedding": encoding
                })
        except Exception as e:
            print(f"[Face Recognizer Error] Failed to process frame: {e}")
            
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
