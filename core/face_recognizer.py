import cv2
import numpy as np
import time
from config import settings

# Try dlib-based face_recognition
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Try InsightFace
try:
    import insightface
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

# Try MediaPipe FaceMesh
try:
    import mediapipe as mp
    import mediapipe.python.solutions.face_mesh as mp_face_mesh
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[Face Recognizer Warning] 'mediapipe' library not available.")

class MemoraFaceRecognizer:
    """
    Identity Anchoring Module (Pillar I).
    Supports multiple backends with automatic fallback:
    1. dlib-based face_recognition (128D)
    2. InsightFace ArcFace
    3. Custom MediaPipe FaceMesh geometric proportions embedding (128D fallback)
    Implements 500ms face gating, a temporal unknown tracker (15-frame buffer),
    and embedding stability averaging.
    """
    def __init__(self, tolerance=settings.FACE_TOLERANCE, mock_mode=False):
        self.tolerance = tolerance
        self.mock_mode = mock_mode
        self.face_mesh = None
        self.face_recognition_active = False
        
        # Gating and temporal consistency states
        self.face_first_seen_time = None
        self.gating_threshold = 0.5  # 500ms steady face filter
        
        # Temporal candidate tracker
        self.unknown_candidates = {}
        self.next_candidate_index = 1

        if self.mock_mode:
            self.backend = "mock"
            print("[Face Recognizer] Initialized mock simulator backend.")
        elif FACE_RECOGNITION_AVAILABLE:
            self.backend = "face_recognition"
            self.face_recognition_active = True
            print("[Face Recognizer] Initialized dlib-based 'face_recognition' backend.")
        elif INSIGHTFACE_AVAILABLE:
            self.backend = "insightface"
            print("[Face Recognizer] Initialized InsightFace backend.")
        elif MEDIAPIPE_AVAILABLE:
            self.backend = "mediapipe"
            try:
                self.face_mesh = mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=5,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("[Face Recognizer] Initialized MediaPipe FaceMesh fallback backend.")
            except Exception as e:
                print(f"[Face Recognizer Warning] Failed to initialize MediaPipe: {e}. Enabling mock fallback.")
                self.mock_mode = True
                self.backend = "mock"
        else:
            print("[Face Recognizer Warning] No computer vision backends available. Forcing mock fallback mode.")
            self.mock_mode = True
            self.backend = "mock"

    def _compute_geometric_embedding(self, landmarks, w, h):
        """
        Custom 128D geometric proportion embedding. Computes scale-normalized
        pairwise distances between stable facial landmarks. Does not unit-normalize,
        preserving absolute ratio differences for threshold discriminativeness.
        """
        key_indices = [4, 152, 33, 263, 61, 291, 70, 300, 10, 0, 17, 6, 234, 454, 133, 362]
        
        points = []
        for idx in key_indices:
            lm = landmarks.landmark[idx]
            points.append([lm.x * w, lm.y * h, lm.z * w])
        points = np.array(points)

        distances = []
        for i in range(16):
            for j in range(i + 1, 16):
                dist = np.linalg.norm(points[i] - points[j])
                distances.append(dist)
        distances = np.array(distances)

        left_eye_outer = points[2]
        right_eye_outer = points[3]
        inter_pupil_dist = np.linalg.norm(left_eye_outer - right_eye_outer)
        
        if inter_pupil_dist > 0:
            distances = distances / inter_pupil_dist

        extra_indices = [21, 54, 162, 127, 251, 284, 389, 356]
        extra_distances = []
        nose_tip = points[0]
        
        for idx in extra_indices:
            lm = landmarks.landmark[idx]
            ep = np.array([lm.x * w, lm.y * h, lm.z * w])
            dist = np.linalg.norm(ep - nose_tip)
            if inter_pupil_dist > 0:
                dist = dist / inter_pupil_dist
            extra_distances.append(dist)
        
        embedding = np.concatenate([distances, np.array(extra_distances)])
        print(f"[Debug Embedding] First 5 values: {embedding[:5]}")
        return embedding

    def process_frame(self, frame, database):
        """
        Processes a BGR camera frame:
        1. Steady gating (face must remain stable for >= 500ms).
        2. Extract face embeddings (dlib, insightface, or MediaPipe custom).
        3. Match with database or assign to temporal unknown tracker.
        4. Average 15 stable frames before creating a new database Anonymous_ID.
        5. Update matched profiles using EMA.
        """
        results = []
        if frame is None:
            return results

        h, w, _ = frame.shape
        now_time = time.time()

        # Decay stale temporal candidates (not seen for > 2 seconds)
        stale_keys = [k for k, v in self.unknown_candidates.items() if now_time - v["last_seen_time"] > 2.0]
        for k in stale_keys:
            del self.unknown_candidates[k]

        # --- MOCK MODE BACKEND ---
        if self.backend == "mock":
            top, right, bottom, left = h // 4, 3 * w // 4, 3 * h // 4, w // 4
            mock_embedding = np.zeros(128)
            face_region = frame[top:bottom, left:right]
            avg_color = face_region.mean(axis=(0, 1)) if face_region.size > 0 else [128.0, 128.0, 128.0]
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
            confidence_pct = 0
            
            if face_id is None:
                face_id = database.register_anonymous(mock_embedding)
                info = database.get_identity(face_id)
                is_new = True
                decision = "NEW PERSON"
                best_match_name = "None"
            else:
                best_match_name = info["display_name"] if info["display_name"] else face_id
                confidence_pct = int(info["confidence"] * 100)
                database.increment_times_seen(face_id)

            print("\n---------------------------------")
            print("Face Detected")
            print(f"Best Match: {best_match_name}")
            print(f"Distance: {dist:.4f}" if dist is not None else "Distance: N/A")
            print(f"Decision: {decision}")
            print(f"Confidence: {confidence_pct}%")
            print("---------------------------------\n")

            results.append({
                "box": (top, right, bottom, left),
                "face_id": face_id,
                "name": info["display_name"],
                "relationship": info["relationship"],
                "is_new": is_new,
                "embedding": mock_embedding
            })
            return results

        # --- REAL DETECTION PIPELINE ---
        detected_faces = []  # list of dicts: {"box": (top, right, bottom, left), "center": (cx, cy), "landmarks_or_crop": ...}

        # 1. Detect faces using active backend
        if self.backend == "face_recognition":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            for box in face_locations:
                top, right, bottom, left = box
                cx, cy = (left + right) // 2, (top + bottom) // 2
                # Get the 128D encoding directly
                encs = face_recognition.face_encodings(rgb_frame, [box])
                if encs:
                    detected_faces.append({
                        "box": box,
                        "center": (cx, cy),
                        "embedding": encs[0]
                    })
        elif self.backend == "mediapipe":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mesh_results = self.face_mesh.process(rgb_frame)
            if mesh_results.multi_face_landmarks:
                for landmarks in mesh_results.multi_face_landmarks:
                    xs = [lm.x * w for lm in landmarks.landmark]
                    ys = [lm.y * h for lm in landmarks.landmark]
                    left_px = int(max(0, min(xs)))
                    right_px = int(min(w - 1, max(xs)))
                    top_px = int(max(0, min(ys)))
                    bottom_px = int(min(h - 1, max(ys)))
                    box = (top_px, right_px, bottom_px, left_px)
                    cx, cy = (left_px + right_px) // 2, (top_px + bottom_px) // 2
                    
                    embedding = self._compute_geometric_embedding(landmarks, w, h)
                    detected_faces.append({
                        "box": box,
                        "center": (cx, cy),
                        "embedding": embedding
                    })

        # Steady Face Gating Filter
        if not detected_faces:
            self.face_first_seen_time = None
            return results

        if self.face_first_seen_time is None:
            self.face_first_seen_time = now_time
            print("[Face Recognizer] Face detected. Calibrating gating filter (500ms)...")
            return results

        elapsed = now_time - self.face_first_seen_time
        if elapsed < self.gating_threshold:
            # Gated: wait for 500ms steady presence
            return results

        # Process each detected face
        for face in detected_faces:
            box = face["box"]
            cx, cy = face["center"]
            embedding = face["embedding"]

            face_id, info, dist = database.find_match(embedding, self.tolerance)
            
            if face_id is not None:
                emb_id = info.get("embedding_row_id") if info else None
                # Successfully recognized in database!
                # Clear any nearby temporal unknown candidates
                matched_cand_key = None
                for k, v in self.unknown_candidates.items():
                    dcx, dcy = v["center"]
                    distance = np.hypot(cx - dcx, cy - dcy)
                    if distance < 80:
                        matched_cand_key = k
                        break
                if matched_cand_key:
                    del self.unknown_candidates[matched_cand_key]

                # Update database embedding using EMA (alpha=0.1)
                database.update_embedding_ema(emb_id, embedding, alpha=0.1)
                # Increment seen counter
                database.increment_times_seen(face_id)
                
                # Fetch fresh profile details
                info = database.get_identity(face_id)
                best_match_name = info["display_name"] if info["display_name"] else face_id
                confidence_pct = int(info["confidence"] * 100)

                print("\n---------------------------------")
                print("Face Detected")
                print(f"Best Match: {best_match_name}")
                print(f"Distance: {dist:.4f}")
                print(f"Decision: RECOGNIZED")
                print(f"Confidence: {confidence_pct}%")
                print("---------------------------------\n")

                results.append({
                    "box": box,
                    "face_id": face_id,
                    "name": info["display_name"],
                    "relationship": info["relationship"],
                    "is_new": False,
                    "embedding": embedding
                })
            else:
                # Step 2: Temporal Consistency Unknown Tracker
                matched_cand_key = None
                for k, v in self.unknown_candidates.items():
                    dcx, dcy = v["center"]
                    distance = np.hypot(cx - dcx, cy - dcy)
                    if distance < 80:
                        matched_cand_key = k
                        break

                if matched_cand_key:
                    candidate = self.unknown_candidates[matched_cand_key]
                    candidate["frames_seen"] += 1
                    candidate["embeddings"].append(embedding)
                    candidate["center"] = (cx, cy)
                    candidate["last_seen_time"] = now_time

                    frames_seen = candidate["frames_seen"]
                    if frames_seen >= 15:
                        # Stability met: average embeddings and register in database
                        avg_embedding = np.mean(candidate["embeddings"], axis=0)
                        new_id = database.register_anonymous(avg_embedding)
                        info = database.get_identity(new_id)
                        
                        print("\n---------------------------------")
                        print("Face Detected")
                        print("Best Match: None")
                        print("Distance: N/A")
                        print("Decision: NEW PERSON")
                        print("Confidence: 0%")
                        print("---------------------------------\n")
                        
                        results.append({
                            "box": box,
                            "face_id": new_id,
                            "name": None,
                            "relationship": None,
                            "is_new": True,
                            "embedding": avg_embedding
                        })
                        del self.unknown_candidates[matched_cand_key]
                    else:
                        # Accumulating frames: do not log in database yet
                        results.append({
                            "box": box,
                            "face_id": None,
                            "name": None,
                            "relationship": None,
                            "is_new": False,
                            "embedding": embedding,
                            "label": f"Detecting... ({frames_seen}/15)"
                        })
                else:
                    # Brand new candidate: create tracker
                    cand_id = f"Temp_Cand_{self.next_candidate_index}"
                    self.next_candidate_index += 1
                    self.unknown_candidates[cand_id] = {
                        "frames_seen": 1,
                        "embeddings": [embedding],
                        "center": (cx, cy),
                        "last_seen_time": now_time
                    }
                    results.append({
                        "box": box,
                        "face_id": None,
                        "name": None,
                        "relationship": None,
                        "is_new": False,
                        "embedding": embedding,
                        "label": "Detecting... (1/15)"
                    })

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
            label_override = res.get("label")

            # Set colors (green for recognized, orange for detecting, red for new)
            is_recognized = name is not None
            if is_recognized:
                color = (0, 255, 0)
                if relationship:
                    label = f"{name} ({relationship})"
                else:
                    label = name
            elif label_override:
                color = (0, 165, 255) # Orange (detecting)
                label = label_override
            else:
                color = (0, 0, 255) # Red (new unconfirmed)
                label = f"New Face: {face_id}"

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
