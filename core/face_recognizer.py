import cv2
import numpy as np
import time

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
    Includes a 500ms steady-gating filter to prevent CPU spikes and database spam.
    """
    def __init__(self, tolerance=0.6, mock_mode=False):
        self.tolerance = tolerance
        self.mock_mode = mock_mode or not MEDIAPIPE_AVAILABLE
        self.face_mesh = None
        
        # Face Gating configuration
        self.face_first_seen_time = None
        self.gating_threshold = 0.5  # 500ms steady confirmation threshold

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

    def _compute_geometric_embedding(self, landmarks, w, h):
        """
        Computes a deterministic, scale-, rotation-, and translation-invariant 128D facial embedding
        from normalized 3D landmarks coordinates by scaling them to pixel dimensions first.
        """
        # 16 stable landmark indices across different areas of the face mesh
        key_indices = [4, 152, 33, 263, 61, 291, 70, 300, 10, 0, 17, 6, 234, 454, 133, 362]
        
        points = []
        for idx in key_indices:
            lm = landmarks.landmark[idx]
            points.append([lm.x * w, lm.y * h, lm.z * w])
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
        extra_indices = [21, 54, 162, 127, 251, 284, 389, 356]
        extra_distances = []
        nose_tip = points[0] # index 4
        
        for idx in extra_indices:
            lm = landmarks.landmark[idx]
            ep = np.array([lm.x * w, lm.y * h, lm.z * w])
            dist = np.linalg.norm(ep - nose_tip)
            if inter_pupil_dist > 0:
                dist = dist / inter_pupil_dist
            extra_distances.append(dist)
        
        # Combine to form the 128D embedding
        embedding = np.concatenate([distances, np.array(extra_distances)])

        # Print the first few values of the embedding for debugging
        print(f"[Debug Embedding] First 5 values: {embedding[:5]}")

        return embedding

    def process_frame(self, frame, database):
        """
        Processes a BGR camera frame.
        1. Fast gate: Checks face presence using FaceMesh (or mock region).
        2. Gating filter: Only proceeds to database check if face is steady for >= 500ms.
        3. Computes 128D geometric embeddings and queries SQLite database to match.
        """
        results = []
        if frame is None:
            return results

        h, w, _ = frame.shape

        if self.mock_mode:
            # Simulated mode: always detect a face in the center of the screen
            top, right, bottom, left = h // 4, 3 * w // 4, 3 * h // 4, w // 4
            
            # Compute mock embedding from face region
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
            decision = "RECOGNIZED"
            best_match_name = "None"
            
            if face_id is None:
                face_id = database.register_anonymous(mock_embedding)
                info = database.get_identity(face_id)
                is_new = True
                decision = "NEW PERSON"
                best_match_name = "None"
            else:
                best_match_name = info["name"] if info["name"] else face_id

            print("\n---------------------------------")
            print("Face detected")
            print("Embedding generated")
            print(f"Best Match: {best_match_name}")
            print(f"Distance: {dist:.4f}" if dist is not None else "Distance: N/A")
            print(f"Threshold: {self.tolerance}")
            print(f"Decision: {decision}")
            print("---------------------------------\n")

            results.append({
                "box": (top, right, bottom, left),
                "face_id": face_id,
                "name": info["name"],
                "relationship": info["relationship"],
                "is_new": is_new,
                "embedding": mock_embedding
            })
            return results

        # Real detection mode using MediaPipe FaceMesh
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mesh_results = self.face_mesh.process(rgb_frame)
            
            if not mesh_results.multi_face_landmarks:
                # No face present, reset the gating timer
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
                # Gated: Face is detected but not steady yet
                return results

            for landmarks in mesh_results.multi_face_landmarks:
                # 1. Determine bounding box
                xs = [lm.x * w for lm in landmarks.landmark]
                ys = [lm.y * h for lm in landmarks.landmark]
                left_px = int(max(0, min(xs)))
                right_px = int(min(w - 1, max(xs)))
                top_px = int(max(0, min(ys)))
                bottom_px = int(min(h - 1, max(ys)))
                box = (top_px, right_px, bottom_px, left_px)

                # 2. Extract 128D embedding
                encoding = self._compute_geometric_embedding(landmarks, w, h)

                # 3. Search in database
                face_id, info, dist = database.find_match(encoding, self.tolerance)
                is_new = False
                decision = "RECOGNIZED"
                best_match_name = "None"
                
                if face_id is None:
                    # Register new anonymous person
                    face_id = database.register_anonymous(encoding)
                    info = database.get_identity(face_id)
                    is_new = True
                    decision = "NEW PERSON"
                    best_match_name = "None"
                else:
                    best_match_name = info["name"] if info["name"] else face_id
                    # Reinforce identity
                    if dist > 0.15 and len(info["embeddings"]) < 10:
                        database.add_embedding_to_identity(face_id, encoding)

                print("\n---------------------------------")
                print("Face detected")
                print("Embedding generated")
                print(f"Best Match: {best_match_name}")
                print(f"Distance: {dist:.4f}" if dist is not None else "Distance: N/A")
                print(f"Threshold: {self.tolerance}")
                print(f"Decision: {decision}")
                print("---------------------------------\n")

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
