# MEMORA (Samsung Anchor) — Subsystem Module Deep Dives & AI Design Specification

This document details the module design, public APIs, failure modes, and AI system mechanisms across all 21 core components of MEMORA (Samsung Anchor) Release Candidate RC1.

---

## PART 3 & PART 8 — SUBSYSTEM MODULE SPECIFICATIONS

### 1. Application & Factory Module
- **File**: [src/application/factory.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/application/factory.py)
- **Purpose**: Assembles the entire MEMORA platform by constructing database, vision, audio, reasoning, and speaker instances.
- **Key API**: `build_application(*, live_hardware=False, database=None, recognizer=None, listener=None, binder=None, speaker=None) -> AnchorCoordinator`
- **Behavior**: Instantiates concrete implementations defaulting to mock hardware mode unless `live_hardware=True` is explicitly specified.

---

### 2. Runtime Manager Module
- **File**: [src/runtime/runtime.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/runtime/runtime.py)
- **Purpose**: Manages application lifecycle, heartbeat logging, and hardware failure isolation.
- **Key API**:
  - `AnchorRuntime.initialize()`: Prepares coordinator & resets queues.
  - `AnchorRuntime.run_continuous(max_cycles=None, cycle_delay=0.1)`: Continuous perception-cognition execution loop.
  - `AnchorRuntime.get_subsystem_statuses() -> Dict[str, str]`: Phase 6 Observability status provider (`READY`, `WARNING (Simulated)`, `DISABLED`, `FAILED`).

---

### 3. Anchor Coordinator Module
- **File**: [src/coordinator/anchor_coordinator.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/coordinator/anchor_coordinator.py)
- **Purpose**: Serves as the central orchestration hub, managing background threads, event bus subscriptions, and queue backpressure.
- **Hardening (RC1)**:
  - `self._cognitive_queue = queue.Queue(maxsize=10)`
  - Drop-oldest policy implemented in `_on_face_detected()` when queue is full.
  - `self.dropped_events_count`: Metric tracking discarded frames.

---

### 4. Vision Subsystem & Face Recognizer
- **File**: [src/vision/face_recognizer.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/vision/face_recognizer.py)
- **Purpose**: Multimodal face detection, 128D embedding extraction, persistent spatial tracking, and FAISS vector matching.
- **Supported Backends**:
  1. `face_recognition` (dlib-based)
  2. InsightFace ArcFace / SCRFD
  3. MediaPipe FaceMesh (Geometric proportion fallback)
  4. Mock Simulator (Synthetic noise arrays)
- **Hardening (RC1)**:
  - Thread-locked with `self._lock = threading.Lock()` to prevent multithread dictionary mutation errors.
  - Multi-frame consensus: `required_consensus_frames = 3` before identity promotion to `RECOGNIZED`.
  - Automatic stale track purging when `missed_frames > 30` or `inactivity > 60s`.

---

### 5. Vector Store & FAISS Subsystem
- **File**: [src/memory/vector_store.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/memory/vector_store.py)
- **Purpose**: Manages 128-dimensional face embedding vectors using FAISS (`IndexFlatL2`).
- **Key API**:
  - `find_match(query_embedding, tolerance=0.6) -> (identity_id, faiss_id, distance)`
  - `add_embedding(identity_id, embedding) -> faiss_id`
  - `update_embedding_ema(faiss_id, new_embedding, alpha=0.1)`
- **Thread Safety**: All operations are protected by `threading.Lock()` to prevent SWIG C++ memory pointer race conditions.

---

### 6. Visual Episodic Memory Engine
- **File**: [src/perception/visual_memory_engine.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/perception/visual_memory_engine.py)
- **Purpose**: Stores spatial locations of personal items (reading glasses, walking cane, keys, remote, medication bottle) observed by the object detector.
- **Key API**: `recall_object_location(query_text, patient_name) -> Dict[str, Any]`
- **Honest Non-Hallucination Policy**: If an item is not found in stored spatial room memories, returns `found=False` with a polite refusal rather than synthesizing a false location.

---

### 7. Cognitive Pipeline & Context Fusion
- **File**: [src/pipeline/cognitive_pipeline.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/pipeline/cognitive_pipeline.py)
- **Purpose**: Executes the 10-stage cognitive cycle: perception, presence check, context fusion, goal inference, attention evaluation, patient state inference, care policy evaluation, visual memory recall, decision trace logging, and audio dispatch.

---

### 8. Patient State Evaluator Module
- **File**: [src/clinical/patient_state.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/clinical/patient_state.py)
- **Purpose**: Evaluates real-time patient emotional and cognitive state.
- **Supported Modes**:
  - `ORIENTED`: Calm, responsive, aware of time and surroundings.
  - `SEARCHING`: Patient is actively looking for a misplaced item.
  - `REPETITIVE`: Patient is asking repetitive questions (e.g., appointment time).
  - `ANXIOUS`: Patient is experiencing emotional distress or confusion.
  - `AWAITING_REMINDER`: Pending scheduled medication dose.
  - `EMERGENCY`: Unsafe behavior, fall, or physical emergency detected.

---

### 9. Care Policy Framework Module
- **File**: [src/clinical/care_policy.py](file:///Users/siddhant_patil/Projects/Samsung_Anchor/src/clinical/care_policy.py)
- **Purpose**: Enforces clinical care principles tailored for dementia caregiving:
  - `ONE_STEP_GUIDANCE`: Delivers concise, single-step actionable instructions.
  - `VALIDATION_THERAPY`: Validates patient feelings without arguing or scolding.
  - `REPETITIVE_REDIRECTION`: Delivers consistent, reassuring answers to repeated questions.
  - `EMERGENCY_ESCALATION`: Immediately alerts caregiver team upon safety hazards.
  - `SUPPORTIVE_SILENCE`: Suppresses unnecessary audio output when patient is calm.
