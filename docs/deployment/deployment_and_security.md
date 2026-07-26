# MEMORA (Samsung Anchor) — Deployment, Security, Privacy & Demonstration Guide

This document details deployment procedures, security architecture, privacy boundaries, automated testing suite breakdown, and operator demonstration scripts for MEMORA (Samsung Anchor) Release Candidate RC1.

---

## PART 9 — TESTING SUITE SPECIFICATION

### Test Suite Structure (174 Passing Tests)

```
tests/
├── test_release_candidate.py          # RC1 P0 controls (queue bounds, thread locks, consensus)
├── test_end_to_end_validation.py      # End-to-end cognitive cycles & clinical scenario suite
├── test_clinical_scenario_validation.py # 10 clinical caregiving scenarios harness
├── test_runtime_completion.py         # Subsystem status reporting & continuous loop tests
├── test_cognitive_pipeline.py         # Pipeline processing & action dispatch
├── test_patient_state_and_care_policy.py # State machine & dementia care principles
├── test_visual_episodic_memory.py     # Honest object location recall
└── test_perception_manager.py         # Face, room, and activity perception integration
```

### Running Automated Test Verification
```bash
# Execute entire test suite (174 tests)
.venv/bin/pytest -v

# Execute dedicated Release Candidate test suite
.venv/bin/pytest tests/test_release_candidate.py -v
```

---

## PART 11 — SECURITY & PRIVACY ARCHITECTURE

### 1. Local Edge Processing Boundary
- **Zero Video / Audio Exfiltration**: Visual frames captured by the camera HAL are processed strictly in local RAM for embedding extraction and face tracking, then immediately overwritten. Raw video streams are never written to disk or transmitted across external networks.
- **Offline Self-Containment**: Face embedding matching (FAISS) and clinical care policy evaluations operate 100% offline without requiring external API connectivity.

### 2. Data Encryption & Storage Security
- SQLite local memory databases (`database.db`) are stored with strict local OS file permission boundaries (`0600`).
- No personally identifiable health data (PHI) is exposed over unauthenticated network sockets. The WebSocket dashboard stream binds to local interface `127.0.0.1`.

---

## PART 12 — DEPLOYMENT & DOCKERIZATION GUIDE

### Docker Deployment Guide

#### `Dockerfile` Specification
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8765

CMD ["python", "app.py", "--simulation", "--dashboard"]
```

#### Build and Run Container
```bash
# Build Docker image
docker build -t memora-anchor:rc1 .

# Run container with dashboard bound to port 8765
docker run -p 8765:8765 memora-anchor:rc1
```

---

## PART 13 — LIVE DEMONSTRATION GUIDE FOR SAMSUNG JUDGES

### Operator Checklist Before Demonstration

1. **Environment Setup**:
   - Ensure Python 3.11 virtual environment is activated (`source .venv/bin/activate`).
   - Open two terminal windows.

2. **Step 1: Clinical Scenario Automated Demonstration**:
   - In Terminal 1, execute:
     ```bash
     python app.py --simulation --scenario
     ```
   - **Expected Output**: Runs all 10 clinical caregiving scenarios, displaying `10/10 PASS` with decision traces for patient arrival, misplaced glasses search, validation therapy, and emergency escalation.

3. **Step 2: Experience Platform Interactive Dashboard**:
   - In Terminal 2, execute:
     ```bash
     python app.py --dashboard --max-cycles 5
     ```
   - **Expected Output**: Opens `http://localhost:8765` in default browser. Show judges real-time panels:
     - **What MEMORA Sees**: Face tracking bounding boxes & room location.
     - **What MEMORA Hears**: Live recognized speech events.
     - **What MEMORA Remembers**: Visual episodic memory tuples.
     - **What MEMORA Believes**: Patient state mode (`ORIENTED`, `SEARCHING`, `ANXIOUS`).
     - **Why MEMORA Responded**: Care policy principle & clinical explainability trace.

4. **Step 3: Live Hardware Mode (If Camera Available)**:
   - Execute:
     ```bash
     python app.py --live-hardware
     ```
   - **Expected Output**: Displays live video feed banner and activates physical webcam face tracking.
