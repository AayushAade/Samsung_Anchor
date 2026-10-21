import cv2
import numpy as np
import time
import os
import threading
from collections import deque

# Rolling window of recent embeddings kept per face track. Tracks previously kept
# every frame's embedding forever and averaged the whole history twice per frame,
# so memory and per-frame time grew without bound while a person stayed in view.
TRACK_EMBEDDING_WINDOW = 30
from config import settings
from src.utils.event_logger import log_event

import logging
logger = logging.getLogger(__name__)

# Try dlib-based face_recognition
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Try InsightFace SCRFD
try:
    from insightface.model_zoo.scrfd import SCRFD
    SCRFD_AVAILABLE = True
except ImportError:
    SCRFD_AVAILABLE = False

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
    if settings.DEBUG:
        logger.warning("[Face Recognizer Warning] 'mediapipe' library not available.")
def compute_iou(boxA, boxB):
    """Computes Intersection-over-Union (IoU) of two bounding boxes (top, right, bottom, left)."""
    tA, rA, bA, lA = boxA
    tB, rB, bB, lB = boxB
    
    xA = max(lA, lB)
    yA = max(tA, tB)
    xB = min(rA, rB)
    yB = min(bA, bB)
    
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (rA - lA) * (bA - tA)
    boxBArea = (rB - lB) * (bB - tB)
    unionArea = boxAArea + boxBArea - interArea
    
    return interArea / float(unionArea) if unionArea > 0 else 0

class MemoraFaceRecognizer:
    """
    Identity Anchoring Module (Pillar I).
    Supports multiple backends with automatic fallback:
    1. dlib-based face_recognition (128D)
    2. InsightFace ArcFace
    3. Custom MediaPipe FaceMesh geometric proportions embedding (128D fallback)
    Implements 500ms face gating, a persistent spatial face tracker,
    and embedding stability averaging.
    """
    def __init__(self, tolerance=settings.FACE_TOLERANCE, mock_mode=False, required_consensus_frames=3):
        self._lock = threading.Lock()
        self.tolerance = tolerance
        self.mock_mode = mock_mode
        # Callable returning whether biometric (face recognition) consent is granted.
        self.consent_check = None
        self.required_consensus_frames = required_consensus_frames
        self.face_mesh = None
        self.face_recognition_active = False
        
        # Gating and temporal consistency states
        self.face_first_seen_time = None
        self.gating_threshold = 0.5  # 500ms steady face filter
        
        # Temporal candidate tracker
        self.unknown_candidates = {}
        self.next_candidate_index = 1
        
        # Active tracks dictionary for persistent spatial tracking and debouncing
        # Keys: track_id / identity_id / face_id
        # Values: {
        #   "state": "UNKNOWN" / "STABILIZING" / "RECOGNIZED",
        #   "box": (top, right, bottom, left),
        #   "center": (cx, cy),
        #   "embeddings": list,
        #   "frames_seen": int,
        #   "missed_frames": int,
        #   "last_seen_time": float,
        #   "recognized_logged": bool,
        #   "confirmed_logged": bool
        # }
        self.active_tracks = {}

        # Only backends that are implemented below and importable are selected. The
        # "mock" backend fabricates a face from the centre of every frame, so it is used
        # only when simulation was requested: on real camera frames, with no working
        # backend, recognition is reported unavailable and detects nothing.
        self.unavailable_reason = None
        self.yunet = None
        self.sface = None
        model_status = None
        if not self.mock_mode:
            from src.vision.face_models import verify_models
            model_status = verify_models()
        if self.mock_mode:
            self.backend = "mock"
            if settings.DEBUG:
                logger.debug("[Face Recognizer] Initialized mock simulator backend.")
        elif model_status is not None and model_status.ready and self._start_sface(model_status):
            self.backend = "sface"
            self.tolerance = settings.SFACE_MATCH_TOLERANCE
        elif FACE_RECOGNITION_AVAILABLE:
            self.backend = "face_recognition"
            self.face_recognition_active = True
            if settings.DEBUG:
                logger.debug("[Face Recognizer] Initialized dlib-based 'face_recognition' backend.")
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
                if settings.DEBUG:
                    logger.debug("[Face Recognizer] Initialized MediaPipe FaceMesh fallback backend.")
            except Exception as e:
                self.backend = "unavailable"
                self.unavailable_reason = f"MediaPipe FaceMesh could not start: {e}"
        else:
            self.backend = "unavailable"
            self.unavailable_reason = (
                "no working face-recognition backend: "
                + (self.unavailable_reason or (model_status.reason() if model_status else "models not checked"))
                + " (see docs/FACE_RECOGNITION.md); dlib 'face_recognition' and MediaPipe FaceMesh are not available")
        if self.backend == "unavailable":
            logger.warning("[Face Recognizer] Face recognition unavailable: %s", self.unavailable_reason)

        # Try loading SCRFD face detector for fast/accurate bounding box extraction
        self.scrfd_detector = None
        if not self.mock_mode and SCRFD_AVAILABLE:
            model_path = os.path.join(settings.BASE_DIR, "assets", "scrfd_500m_bnkps.onnx")
            if os.path.exists(model_path):
                try:
                    self.scrfd_detector = SCRFD(model_file=model_path)
                    self.scrfd_detector.prepare(ctx_id=-1) # -1 is CPU inference
                    if settings.DEBUG:
                        logger.debug("[Face Recognizer] Loaded SCRFD face detection model.")
                except Exception as e:
                    if settings.DEBUG:
                        logger.warning(f"[Face Recognizer Warning] Failed to initialize SCRFD model: {e}")
    @staticmethod
    def _not_sure(box) -> dict:
        return {"box": box, "face_id": None, "name": None, "relationship": None, "is_new": False,
                "label": "Not sure who this is"}

    def _start_sface(self, model_status) -> bool:
        """Create the OpenCV YuNet detector and SFace recogniser from verified model files."""
        try:
            self.yunet = cv2.FaceDetectorYN.create(model_status.detector, "", (320, 320),
                                                   settings.FACE_DETECTION_MIN_SCORE, 0.3, 50)
            self.sface = cv2.FaceRecognizerSF.create(model_status.recognizer, "")
            return True
        except Exception as e:  # e.g. a model that this OpenCV build cannot run
            self.yunet = self.sface = None
            self.unavailable_reason = f"YuNet/SFace models could not be loaded by OpenCV {cv2.__version__}: {e}"
            return False

    def _sface_detect(self, frame, compute_embeddings: bool) -> list:
        """YuNet detection, SFace alignment and 128-D L2-normalised features."""
        h, w = frame.shape[:2]
        self.yunet.setInputSize((w, h))
        _, faces = self.yunet.detect(frame)
        out = []
        for row in (faces if faces is not None else []):
            x, y, fw, fh, score = float(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[-1])
            if score < settings.FACE_DETECTION_MIN_SCORE or min(fw, fh) < settings.FACE_MIN_SIZE_PX:
                continue
            left, top = max(0, int(x)), max(0, int(y))
            right, bottom = min(w - 1, int(x + fw)), min(h - 1, int(y + fh))
            embedding = None
            if compute_embeddings:
                feature = np.asarray(self.sface.feature(self.sface.alignCrop(frame, row)), dtype=np.float32).reshape(-1)
                norm = float(np.linalg.norm(feature))
                if feature.size != 128 or norm == 0:
                    continue
                embedding = feature / norm
            out.append({"box": (top, right, bottom, left), "center": ((left + right) // 2, (top + bottom) // 2),
                        "embedding": embedding, "score": score})
        return out

    def get_diagnostics(self) -> dict:
        return {
            "backend": self.backend,
            "unavailable_reason": self.unavailable_reason,
            "mock_mode": self.mock_mode,
            "scrfd_active": self.scrfd_detector is not None,
            "tolerance": self.tolerance,
            "active_tracks_count": len(self.active_tracks),
        }

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
        if settings.DEBUG:
            logger.debug(f"[Debug Embedding] First 5 values: {embedding[:5]}")
        return embedding

    def _update_missed_tracks(self, now_time, database, associated_tracks=set()):
        """Updates and decays tracks that were not detected in the current frame."""
        stale_keys = []
        for track_id, track in list(self.active_tracks.items()):
            if track_id not in associated_tracks:
                track["missed_frames"] += 1
                mf = track["missed_frames"]
                last_seen_diff = now_time - track.get("last_seen_time", now_time)
                if mf <= 30 and last_seen_diff <= 60.0:
                    if settings.DEBUG:
                        logger.debug(f"Keeping [{track_id}] alive: missed_frames = {mf}/30")
                else:
                    info_t = database.get_identity(track_id)
                    disp_t = info_t["display_name"] if (info_t and info_t.get("status") == "confirmed") else track_id
                    logger.debug(f"Removing [{track_id}] because: missed_frames = {mf} - timeout exceeded")
                    log_event("face_leave", f"Face leaves scene: [{disp_t}]")
                    stale_keys.append(track_id)
        for k in stale_keys:
            if k in self.active_tracks:
                del self.active_tracks[k]

    def process_frame(self, frame, database):
        """Thread-safe frame processing entry point."""
        with self._lock:
            return self._process_frame_internal(frame, database)

    def _process_frame_internal(self, frame, database):
        """
        Processes a BGR camera frame:
        1. Extract face embeddings (dlib, insightface, or MediaPipe custom).
        2. Bounding box association (IoU & Center distance).
        3. Match with database or assign to temporal unknown tracker.
        4. Average 15 stable frames before creating a new database Anonymous_ID.
        5. Missed frames decay with 30-frame (1 second) hysteresis.
        """
        results = []
        if frame is None:
            return results

        if isinstance(frame, dict):
            if frame.get("raw_frame") is not None:
                frame = frame["raw_frame"]
            else:
                h = frame.get("height", 720)
                w = frame.get("width", 1280)
                frame = np.zeros((h, w, 3), dtype=np.uint8)

        h, w, _ = frame.shape
        now_time = time.time()

        # 1. Detect faces using active backend. Without biometric consent no face
        # embedding is computed at all (sface backend): faces are only located.
        consent_ok = self.consent_check is None or bool(self.consent_check())
        detected_faces = []

        if self.backend == "sface":
            detected_faces = self._sface_detect(frame, compute_embeddings=consent_ok)

        elif self.backend == "mock":
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
                
            detected_faces.append({
                "box": (top, right, bottom, left),
                "center": ((left + right) // 2, (top + bottom) // 2),
                "embedding": mock_embedding
            })

        elif self.backend == "face_recognition":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            face_locations = []
            if self.scrfd_detector is not None:
                try:
                    bboxes, kpss = self.scrfd_detector.detect(frame, threshold=0.5)
                    if bboxes is not None:
                        for bbox in bboxes:
                            xmin, ymin, xmax, ymax, score = bbox
                            top = max(0, int(ymin))
                            right = min(w - 1, int(xmax))
                            bottom = min(h - 1, int(ymax))
                            left = max(0, int(xmin))
                            face_locations.append((top, right, bottom, left))
                except Exception as e:
                    if settings.DEBUG:
                        logger.warning(f"[Face Recognizer Warning] SCRFD detection failed: {e}. Falling back to dlib.")
                    face_locations = face_recognition.face_locations(rgb_frame)
            else:
                face_locations = face_recognition.face_locations(rgb_frame)

            for box in face_locations:
                top, right, bottom, left = box
                cx, cy = (left + right) // 2, (top + bottom) // 2
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

        if not detected_faces:
            self._update_missed_tracks(now_time, database)
            return results

        # Biometric consent: without it, faces are neither matched against stored
        # identities nor enrolled, and no embeddings are written. The runtime
        # assembly (AnchorCoordinator) sets consent_check; standalone library use
        # leaves it unset.
        if not consent_ok:
            return [{"box": d["box"], "face_id": None, "name": None, "relationship": None,
                     "is_new": False, "label": "Face recognition is off (no consent)"}
                    for d in detected_faces]

        # Frame counter increment
        if not hasattr(self, "frame_counter"):
            self.frame_counter = 0
        self.frame_counter += 1

        # --- TRACK ASSOCIATION PIPELINE ---
        unassociated_detections = list(detected_faces)
        associated_tracks = set()

        # Step 1: Match detections to existing active tracks (IoU / Distance)
        for track_id, track in list(self.active_tracks.items()):
            track_box = track["box"]
            track_center = track["center"]
            
            best_det_idx = -1
            best_det_score = -1.0
            
            if settings.DEBUG:
                logger.debug(f"\n--- Association Check for Track [{track_id}] (Frame {self.frame_counter}) ---")
            
            for idx, det in enumerate(unassociated_detections):
                iou = compute_iou(det["box"], track_box)
                dist = np.hypot(det["center"][0] - track_center[0], det["center"][1] - track_center[1])
                
                # Compute embedding distance for debugging
                emb_dist = 999.0
                if track["embeddings"] and len(det["embedding"]) > 0:
                    track_avg_emb = np.mean(track["embeddings"], axis=0)
                    emb_dist = float(np.linalg.norm(det["embedding"] - track_avg_emb))

                is_match = False
                score = 0.0
                if iou > 0.2:
                    is_match = True
                    score = iou
                elif dist < 100:
                    is_match = True
                    score = 1.0 / (dist + 1)
                
                if settings.DEBUG:
                    logger.debug(f"Detection {idx}:")
                    logger.debug(f"  IoU = {iou:.3f}")
                    logger.debug(f"  Center Distance = {dist:.1f}px")
                    logger.debug(f"  Embedding Distance = {emb_dist:.3f}")
                    logger.debug(f"  Spatial Match = {is_match} (score = {score:.3f})")
                    
                if is_match and score > best_det_score:
                    best_det_score = score
                    best_det_idx = idx
            
            if best_det_idx != -1:
                det = unassociated_detections.pop(best_det_idx)
                associated_tracks.add(track_id)
                
                # Update persistent track details
                track["box"] = det["box"]
                track["center"] = det["center"]
                track["missed_frames"] = 0
                track["last_seen_time"] = now_time
                track["embeddings"].append(det["embedding"])
                track["frames_seen"] += 1
                
                # Compute embedding distance for the associated detection
                emb_dist = 999.0
                if len(track["embeddings"]) > 1 and len(det["embedding"]) > 0:
                    track_avg_emb = np.mean(list(track["embeddings"])[:-1], axis=0)
                    emb_dist = float(np.linalg.norm(det["embedding"] - track_avg_emb))

                # Print exact requested format
                if settings.DEBUG:
                    logger.debug(f"\nFrame {self.frame_counter}")
                    logger.debug(f"Detection {best_det_idx}")
                    logger.debug(f"\nAssociated with:")
                    logger.debug(f"{track_id}")
                    logger.debug(f"\nIoU = {compute_iou(det['box'], track_box):.3f}")
                    logger.debug(f"\nCenter Distance = {np.hypot(det['center'][0] - track_center[0], det['center'][1] - track_center[1]):.1f}")
                    logger.debug(f"\nEmbedding Distance = {emb_dist:.3f}")
                    logger.debug(f"\nmatched = True")
                    logger.debug(f"\nReset missed_frames = 0\n")
                
                # State transitions
                if track["state"] == "STABILIZING" or track["state"] == "UNKNOWN":
                    track["state"] = "STABILIZING"
                    if track["frames_seen"] >= 15:
                        avg_embedding = np.mean(track["embeddings"], axis=0)
                        # Re-check before enrolling: the averaged face may match a known person
                        # (join that identity) or resemble several (never enrol a duplicate).
                        margin = settings.SFACE_AMBIGUITY_MARGIN if self.backend == "sface" else 0.0
                        recheck = database.match_face(avg_embedding, self.tolerance, margin)
                        if recheck["status"] == "ambiguous":
                            track["state"] = "AMBIGUOUS"
                            results.append(self._not_sure(track["box"]))
                            continue
                        is_new_identity = recheck["status"] != "match"
                        new_id = database.register_anonymous(avg_embedding) if is_new_identity else recheck["identity_id"]
                        info = database.get_identity(new_id)

                        log_event("cand_promote", f"Unknown candidate [{track_id}] promoted to [{new_id}] after 15 stable frames")
                        log_event("face_enter", f"Face enters scene: [{new_id}]")
                        
                        # Promote track to RECOGNIZED state and re-key
                        self.active_tracks[new_id] = {
                            "state": "RECOGNIZED",
                            "box": track["box"],
                            "center": track["center"],
                            "embeddings": track["embeddings"],  # keep the bounded deque
                            "frames_seen": track["frames_seen"],
                            "missed_frames": 0,
                            "last_seen_time": now_time,
                            "recognized_logged": True,
                            "confirmed_logged": False
                        }
                        associated_tracks.add(new_id)
                        del self.active_tracks[track_id]
                        
                        results.append({
                            "box": track["box"],
                            "face_id": new_id,
                            "name": None if is_new_identity else (info or {}).get("display_name"),
                            "relationship": None if is_new_identity else (info or {}).get("relationship"),
                            "is_new": is_new_identity,
                            "embedding": avg_embedding
                        })
                    else:
                        results.append({
                            "box": track["box"],
                            "face_id": None,
                            "name": None,
                            "relationship": None,
                            "is_new": False,
                            "embedding": det["embedding"],
                            "label": f"Detecting... ({track['frames_seen']}/15)"
                        })
                        
                elif track["state"] == "AMBIGUOUS":
                    results.append(self._not_sure(track["box"]))

                elif track["state"] == "RECOGNIZED":
                    # Known tracked identity: check database match to apply reinforcement/EMA
                    face_id, info, d = database.find_match(det["embedding"], self.tolerance)
                    
                    if face_id is not None:
                        emb_id = info.get("embedding_row_id") if info else None
                        database.update_embedding_ema(emb_id, det["embedding"], alpha=0.1)
                        database.increment_times_seen(face_id)
                        
                        info = database.get_identity(face_id)
                        is_confirmed = info.get("status") == "confirmed" if info else False
                        best_match_name = info.get("display_name") if (info and info.get("display_name")) else face_id
                        confidence_pct = int(info.get("confidence", 0.9) * 100) if info else 90
                        
                        if not track["recognized_logged"]:
                            if is_confirmed:
                                log_event("recognized", f"[{best_match_name}] recognized (Recognition Confidence: {confidence_pct}%)")
                            else:
                                log_event("recognized", f"[{face_id}] recognized (Distance: {d:.3f})")
                            track["recognized_logged"] = True
                            
                        if is_confirmed and not track["confirmed_logged"]:
                            log_event("confirmed", f"[{best_match_name}] identity confirmed (Confidence: {confidence_pct}%)")
                            track["confirmed_logged"] = True
                            
                        results.append({
                            "box": track["box"],
                            "face_id": face_id,
                            "name": info.get("display_name") if info else None,
                            "relationship": info.get("relationship") if info else None,
                            "is_new": False,
                            "embedding": det["embedding"]
                        })
                    else:
                        # Database lookup failed/exceeded threshold temporarily, but WE KEEP the recognized identity!
                        info = database.get_identity(track_id)
                        disp_name = info.get("display_name") if (info and info.get("display_name")) else track_id
                        
                        results.append({
                            "box": track["box"],
                            "face_id": track_id,
                            "name": info.get("display_name") if info else None,
                            "relationship": info.get("relationship") if info else None,
                            "is_new": False,
                            "embedding": det["embedding"]
                        })

        # Step 2: Create new tracks for unassociated detections
        for det in unassociated_detections:
            margin = settings.SFACE_AMBIGUITY_MARGIN if self.backend == "sface" else 0.0
            match = database.match_face(det["embedding"], self.tolerance, margin)
            face_id, info, dist = match["identity_id"], match["info"], match["distance"]

            if match["status"] == "ambiguous":
                cand_id = f"Ambiguous_{self.next_candidate_index}"
                self.next_candidate_index += 1
                self.active_tracks[cand_id] = {
                    "state": "AMBIGUOUS", "box": det["box"], "center": det["center"],
                    "embeddings": deque([det["embedding"]], maxlen=TRACK_EMBEDDING_WINDOW),
                    "frames_seen": 1, "missed_frames": 0, "last_seen_time": now_time,
                    "recognized_logged": False, "confirmed_logged": False}
                associated_tracks.add(cand_id)
                log_event("ambiguous", f"Face resembles more than one known person [{cand_id}]; not named")
                results.append(self._not_sure(det["box"]))
                continue

            if face_id is not None:
                is_confirmed = info.get("status") == "confirmed" if info else False
                best_match_name = info.get("display_name") if (info and info.get("display_name")) else face_id
                confidence_pct = int(info.get("confidence", 0.9) * 100) if info else 90
                
                is_consensus = (self.required_consensus_frames <= 1) or self.mock_mode
                initial_state = "RECOGNIZED" if is_consensus else "STABILIZING"
                
                log_event("face_enter", f"Face enters scene: [{best_match_name}]")
                if is_confirmed:
                    log_event("recognized", f"[{best_match_name}] recognized (Recognition Confidence: {confidence_pct}%)")
                else:
                    log_event("recognized", f"[{face_id}] recognized (Distance: {dist:.3f})")
                
                self.active_tracks[face_id] = {
                    "state": initial_state,
                    "box": det["box"],
                    "center": det["center"],
                    "embeddings": deque([det["embedding"]], maxlen=TRACK_EMBEDDING_WINDOW),
                    "frames_seen": 1,
                    "consensus_count": 1,
                    "missed_frames": 0,
                    "last_seen_time": now_time,
                    "recognized_logged": True,
                    "confirmed_logged": is_confirmed
                }
                associated_tracks.add(face_id)
                
                results.append({
                    "box": det["box"],
                    "face_id": face_id if is_consensus else None,
                    "name": info.get("display_name") if (info and is_consensus) else None,
                    "relationship": info.get("relationship") if (info and is_consensus) else None,
                    "is_new": False,
                    "embedding": det["embedding"]
                })
            else:
                if self.backend == "mock":
                    new_id = database.register_anonymous(det["embedding"])
                    info = database.get_identity(new_id)
                    log_event("face_enter", f"Face enters scene: [{new_id}]")
                    self.active_tracks[new_id] = {
                        "state": "RECOGNIZED",
                        "box": det["box"],
                        "center": det["center"],
                        "embeddings": deque([det["embedding"]], maxlen=TRACK_EMBEDDING_WINDOW),
                        "frames_seen": 1,
                        "missed_frames": 0,
                        "last_seen_time": now_time,
                        "recognized_logged": True,
                        "confirmed_logged": False
                    }
                    associated_tracks.add(new_id)
                    results.append({
                        "box": det["box"],
                        "face_id": new_id,
                        "name": None,
                        "relationship": None,
                        "is_new": True,
                        "embedding": det["embedding"]
                    })
                else:
                    # Brand new unknown candidate: initialize tracker
                    cand_id = f"Temp_Cand_{self.next_candidate_index}"
                    self.next_candidate_index += 1
                    
                    self.active_tracks[cand_id] = {
                        "state": "UNKNOWN",
                        "box": det["box"],
                        "center": det["center"],
                        "embeddings": deque([det["embedding"]], maxlen=TRACK_EMBEDDING_WINDOW),
                        "frames_seen": 1,
                        "missed_frames": 0,
                        "last_seen_time": now_time,
                        "recognized_logged": False,
                        "confirmed_logged": False
                    }
                    associated_tracks.add(cand_id)
                    log_event("cand_create", f"Unknown candidate [{cand_id}] created (1/15 stable frames)")
                    
                    # Print exact requested format
                    if settings.DEBUG:
                        logger.debug(f"\nFrame {self.frame_counter}")
                        logger.debug("No existing track matched.")
                        logger.debug("\nCreating Temp_Candidate.\n")
                    
                    results.append({
                        "box": det["box"],
                        "face_id": None,
                        "name": None,
                        "relationship": None,
                        "is_new": False,
                        "embedding": det["embedding"],
                        "label": "Detecting... (1/15)"
                    })

        # Step 3: Missed frames update
        self._update_missed_tracks(now_time, database, associated_tracks)

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

            is_recognized = name is not None or (face_id is not None and not label_override)
            if is_recognized:
                color = (0, 255, 0)
                disp_name = name if name else face_id
                if relationship:
                    label = f"{disp_name} ({relationship})"
                else:
                    label = disp_name
            elif label_override:
                color = (0, 165, 255)
                label = label_override
            else:
                color = (0, 0, 255)
                label = f"New Face: {face_id}"

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
