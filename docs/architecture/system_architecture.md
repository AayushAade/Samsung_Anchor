# MEMORA (Samsung Anchor) — System Architecture & Data Flow Specification

This document provides the definitive architectural reference for MEMORA (Samsung Anchor) Release Candidate RC1.

---

## PART 2 — SYSTEM ARCHITECTURE

### 1. High-Level Architecture
MEMORA is structured as a decoupled, event-driven 4-tier pipeline:
1. **Perception Layer (Edge HAL & Vision/Audio Pipelines)**: Captures video frames and audio chunks, performs face recognition, object tracking, and voice activity detection.
2. **Cognitive & Memory Layer (Context Fusion & SQLite/FAISS)**: Fuses spatial, temporal, social, and visual memory providers into a unified `CognitiveContext`.
3. **Clinical Governance Layer (Patient State & Care Policy)**: Evaluates patient emotional/cognitive state and selects non-confrontational dementia care policies.
4. **Action & Observability Layer (Speaker Dispatch & Dashboard)**: Executes audio speech output and streams structured `ClinicalDecisionTrace` events over WebSockets.

```mermaid
graph TD
    A[Hardware Sensors: Camera / Mic] --> B[Hardware Abstraction Layer HAL]
    B --> C[SensorBus Event Dispatcher]
    C --> D[Perception Manager]
    D --> E[Face Tracker & Vector Search FAISS]
    D --> F[Visual Episodic Memory Engine]
    E & F --> G[Context Fusion Engine]
    G --> H[Patient State Evaluator]
    H --> I[Care Policy Framework]
    I --> J[Clinical Decision Trace Logger]
    J --> K[Action Dispatcher / Speaker HAL]
    J --> L[WebSockets Experience Dashboard http://localhost:8765]
```

---

### 2. Layered Architecture

```mermaid
classDiagram
    class PerceptionLayer {
        +CameraPipeline
        +AudioPipeline
        +MemoraFaceRecognizer
        +ObjectDetector
        +FaceTracker
    }
    class CognitionLayer {
        +CognitivePipeline
        +ContextFusionEngine
        +PresenceEngine
        +GoalInferenceEngine
        +VisualEpisodicMemoryEngine
    }
    class ClinicalGovernanceLayer {
        +PatientStateEvaluator
        +CarePolicyFramework
        +ClinicalDecisionTraceLogger
        +EmergencyManager
    }
    class ActionAndObservabilityLayer {
        +InteractionManager
        +SpeakerDevice
        +CognitiveStream
        +ExperienceServer
    }

    PerceptionLayer --> CognitionLayer
    CognitionLayer --> ClinicalGovernanceLayer
    ClinicalGovernanceLayer --> ActionAndObservabilityLayer
```

---

### 3. Runtime & Concurrency Architecture

To guarantee that heavy cognitive reasoning never blocks physical camera frame acquisition, MEMORA utilizes a multi-threaded asynchronous worker pattern:

```mermaid
sequenceDiagram
    autonumber
    participant Cam as Camera HAL Thread
    participant Coord as AnchorCoordinator
    participant Queue as Cognitive Queue (maxsize=10)
    participant Worker as Cognitive Worker Thread
    participant Pipe as CognitivePipeline
    participant DB as SQLite / FAISS DB

    Cam->>Coord: process_frame(frame)
    Coord->>Coord: recognizer.process_frame()
    Coord->>Queue: put(face_event) [Drop-oldest if full]
    Worker->>Queue: get(timeout=0.1)
    Worker->>Pipe: process(recognition_payload)
    Pipe->>DB: Query Context & Memories (Thread-Locked)
    Pipe->>Worker: InteractionAction(SPEAK/SILENCE)
    Worker->>Coord: dispatch_action()
```

---

## PART 4 — DATA FLOW SPECIFICATION

### 1. Primary Perception-to-Action Signal Flow

```
[Raw Frame / Audio Chunk]
           │
           ▼
[1. Hardware Adapter (.read())]
           │
           ▼
[2. SensorBus Event ("face_detected")]
           │
           ▼
[3. Bounded Queue (maxsize=10)]  ──► [Drop-Oldest Strategy if full]
           │
           ▼
[4. PerceptionManager] ──► Updates FaceTracker & RoomTracker
           │
           ▼
[5. ContextFusionEngine] ──► Consolidates Identity, Memory, Temporal Context
           │
           ▼
[6. PatientStateEvaluator] ──► Infers Mode (ORIENTED/SEARCHING/ANXIOUS/EMERGENCY)
           │
           ▼
[7. CarePolicyFramework] ──► Enforces Principles (Validation Therapy, One-Step)
           │
           ▼
[8. Visual Memory Recall] ──► Honest location lookup for misplaced items
           │
           ▼
[9. ClinicalDecisionTrace] ──► Logs trace & emits event over WebSocket
           │
           ▼
[10. Speaker HAL] ──► Dispatches audio speech output
```

---

### 2. Identity & Vector Memory Flow

1. **Detection**: Bounding box extracted by SCRFD, dlib, or MediaPipe.
2. **Embedding**: 128-dimensional floating point vector computed.
3. **Similarity Search**: `FaissVectorStore.find_match(query, tolerance=0.6)` executed under `threading.Lock`.
4. **Temporal Consensus**: Candidate identity must maintain match stability for `N=3` consecutive frames (`required_consensus_frames`).
5. **Reinforcement**: Exponential Moving Average (EMA) update applied to confirmed embeddings.

---

### 3. Visual Episodic Memory Recall Flow

```mermaid
graph LR
    A[User Query: Where are my reading glasses?] --> B[VisualEpisodicMemoryEngine]
    B --> C{Contains Item Keyword?}
    C -- Yes --> D[Query SQLite Database]
    C -- No --> E[Pass to Standard Dialogue Planner]
    D --> F{Item Found in Room Memory?}
    F -- Found --> G[Return Location: on the coffee table in Living Room]
    F -- Not Found --> H[Return Honest Refusal: I haven't seen your reading glasses]
```
