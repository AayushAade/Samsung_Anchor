# MEMORA (Samsung Anchor) — Operations Manual & Control Plane Guide

**Phase 20 Implementation** — Operational Control Plane, Live Observability & Production Demonstration Platform.

---

## 1. Overview & Operational Architecture

The **MEMORA Operational Control Plane** provides real-time system orchestration, operational event broadcasting, pre-demo diagnostics, pre-flight startup validation, and demonstration session recording.

```
[System Orchestrator] (src/operations/orchestrator.py)
         │
         ├──────── Subsystem Registry (Vision, Memory, Recognizer, FAISS, Audio, Speaker)
         ├──────── Operational Event Bus (src/operations/operational_event_bus.py)
         ├──────── Pre-Demo Health Diagnostics (health_check.py & startup_validator.py)
         ├──────── Session Recorder (src/operations/session_recorder.py)
         └──────── Live Web Dashboard & WebSockets (experience/server.py & port 8765)
```

---

## 2. One-Command Operational CLI Reference

### 1. Pre-Demo Diagnostic Health Check
```bash
# Execute pre-demo diagnostic health check across 6 critical subsystems
python health_check.py
```
- Verifies Python version, package dependencies, SQLite ORM database, FAISS vector index, OpenCV webcam HAL, and WebSockets port 8765 availability.
- Outputs clean `PASS`, `WARNING`, or `FAIL` status with actionable remediation guidance.

### 2. Demo Operator Control Console
```bash
# Interactive operator console
python operate.py

# Non-interactive CLI flags
python operate.py --health     # Run diagnostic health check
python operate.py --demo       # Run master demo mode (5 scenarios)
python operate.py --validate   # Run validation framework & benchmarks
python operate.py --status     # Display system orchestrator subsystem health
python operate.py --export     # Export recorded demonstration session artifacts
```

### 3. Master Automatic Demo Mode
```bash
python demo_mode.py
```

---

## 3. Subsystem Health & Event Schema

### Subsystem Operational States
- `READY` / `HEALTHY`: Subsystem is operating normally with zero errors.
- `WARNING`: Operating with fallback mechanisms (e.g., Simulated camera fallback).
- `FAILED`: Subsystem encountered a critical failure requiring operator attention.
- `DISABLED`: Subsystem intentionally disabled.

### Operational Event Bus Events
- `RecognitionCompleted`: Face recognition match event completed.
- `MemoryRetrieved`: Visual episodic memory location recall completed.
- `ObjectDetected`: YOLOv8 or heuristic object detected in frame.
- `PatientStateChanged`: Patient cognitive mode transition (`ORIENTED`, `SEARCHING`, `REPETITIVE`, `ANXIOUS`).
- `CarePolicySelected`: Clinical care principle selected (`Validation Therapy`, `One-Step Guidance`).
- `SubsystemStarted` / `SubsystemFailed`: Subsystem lifecycle events.

---

## 4. Session Recording & Replay Artifacts

Every demonstration session recorded via `SessionRecorder` outputs dual artifacts:
1. `validation/artifacts/session_<timestamp>.json`: Complete machine-readable event sequence JSON payload.
2. `validation/artifacts/session_<timestamp>.md`: Formatted Markdown event sequence log for presentation review.
