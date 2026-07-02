import cv2
import numpy as np

try:
    import mediapipe as mp
    import mediapipe.python.solutions.face_mesh as mp_face_mesh
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[Face Recognizer Warning] 'mediapipe' library not available. Face Recognition will run in simulated fallback mode.")

class MemoraFaceRecognizer:
    """
    Identity Anchoring Module (Pillar I).
    Uses MediaPipe FaceMesh to detect faces and compute deterministic, scale-invariant
    128-dimensional biometric embeddings based on facial proportion geometry.
    Includes a complete mock mode fallback for testing and headless environments.
    """
    def __init__(self, tolerance=0.6, mock_mode=False):
        self.tolerance = tolerance
        self.mock_mode = mock_mode or not MEDIAPIPE_AVAILABLE
        self.face_mesh = None

        if not self.mock_mode:
            try:
                self.face_mesh = mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=5,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("[Face Recognizer] MediaPipe FaceMesh initialized successfully.")
            except Exception as e:
                print(f"[Face Recognizer Warning] Failed to initialize MediaPipe FaceMesh: {e}. Enabling mock fallback.")
                self.mock_mode = True

    def _compute_geometric_embedding(self, landmarks):
        """
        Computes a deterministic, scale-, rotation-, and translation-invariant 128D facial embedding
        from normalized 3D landmarks coordinates.
        """
        # 16 stable landmark indices across different areas of the face mesh
        # 4: nose tip
        # 152: chin
        # 33: left eye outer corner
        # 263: right eye outer corner
        # 61: left mouth corner
        # 291: right mouth corner
        # 70: left eyebrow outer end
        # 300: right eyebrow outer end
        # 10: forehead center
        # 0: upper lip center
        # 17: lower lip center
        # 6: nose bridge top
        # 234: left cheek
        # 454: right cheek
        # 133: left eye inner corner
        # 362: right eye inner corner
        key_indices = [4, 152, 33, 263, 61, 291, 70, 300, 10, 0, 17, 6, 234, 454, 133, 362]
        
        points = []
        for idx in key_indices:
            lm = landmarks.landmark[idx]
            points.append([lm.x, lm.y, lm.z])
        points = np.array(points) # shape: (16, 3)

        # Calculate all pairwise distances (16 * 15 / 2 = 120 distances)
        distances = []
        for i in range(16):
            for j in range(i + 1, 16):
                dist = np.linalg.norm(points[i] - points[j])
                distances.append(dist)
        distances = np.array(distances)

        # Scale normalization: divide by inter-pupillary distance (between outer eye corners: index 33 and 263)
        left_eye_outer = points[2]  # index 33
        right_eye_outer = points[3] # index 263
        inter_pupil_dist = np.linalg.norm(left_eye_outer - right_eye_outer)
        
        if inter_pupil_dist > 0:
            distances = distances / inter_pupil_dist

        # Extra 8 ratios to pad the embedding to exactly 128 dimensions
        # We select 8 additional landmarks to calculate their scale-normalized distance from the nose tip
        extra_indices = [21, 54, 162, 127, 251, 284, 389, 356]
        extra_distances = []
        nose_tip = points[0] # index 4
        
        for idx in extra_indices:
            lm = landmarks.landmark[idx]
            ep = np.array([lm.x, lm.y, lm.z])
            dist = np.linalg.norm(ep - nose_tip)
            if inter_pupil_dist > 0:
                dist = dist / inter_pupil_dist
            extra_distances.append(dist)
        
        # Combine to form the 128D embedding
        embedding = np.concatenate([distances, np.array(extra_distances)])

        # Unit normalize the vector so that Euclidean distance queries are clean and bounded in [0, 2]
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def process_frame(self, frame, database):
        """
        Processes a BGR camera frame.
        1. Detects faces using MediaPipe FaceMesh
        2. Computes 128D geometric embeddings
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
            # We will simulate detecting a face in the center of the screen
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

        # Real detection mode using MediaPipe
        try:
            # Convert frame from BGR (OpenCV format) to RGB (MediaPipe format)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process face mesh
            mesh_results = self.face_mesh.process(rgb_frame)
            
            if not mesh_results.multi_face_landmarks:
                return results

            for landmarks in mesh_results.multi_face_landmarks:
                # 1. Determine bounding box (top, right, bottom, left) from min/max coordinates
                xs = [lm.x * w for lm in landmarks.landmark]
                ys = [lm.y * h for lm in landmarks.landmark]
                left_px = int(max(0, min(xs)))
                right_px = int(min(w - 1, max(xs)))
                top_px = int(max(0, min(ys)))
                bottom_px = int(min(h - 1, max(ys)))
                box = (top_px, right_px, bottom_px, left_px)

                # 2. Extract 128D embedding
                encoding = self._compute_geometric_embedding(landmarks)

                # 3. Search in database
                face_id, info, dist = database.find_match(encoding, self.tolerance)
                is_new = False
                
                if face_id is None:
                    # Register new anonymous person
                    face_id = database.register_anonymous(encoding)
                    info = database.get_identity(face_id)
                    is_new = True
                else:
                    # Reinforce identity
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
            print(f"[Face Recognizer Error] MediaPipe processing failed: {e}")
            
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
