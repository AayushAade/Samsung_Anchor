# MEMORA Master Architecture Guide

- **Document Version**: 2.0.0
- **Scope**: Complete Architectural Architecture Specification (Phases 21–27)

---

## 1. System Overview

MEMORA is an AI-powered external cognitive memory assistant and adaptive companion designed for patients suffering from Alzheimer's disease and cognitive impairment.

The architecture is organized into **6 standardized cognitive layers** operating above hardware perception and below clinical safety guardrails:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MEMORA MASTER ARCHITECTURE                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    1. PERCEPTION & SENSOR HAL                         │  │
│  │  OpenCV Video Pipeline • FAISS 128D Face Rec • SensorBus HAL Adapters  │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────▼────────────────────────────────────┐  │
│  │              2. COGNITIVE OPERATING SYSTEM (COS)                      │  │
│  │  Working Memory (TTL) • Attention Manager • Cognitive Kernel          │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────▼────────────────────────────────────┐  │
│  │                 3. COGNITIVE REASONING ENGINE                         │  │
│  │  Cognitive Blackboard • Confidence Engine • Conflict Detector         │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────▼────────────────────────────────────┐  │
│  │                 4. EXECUTIVE FUNCTION FRAMEWORK                       │  │
│  │  Goal Hierarchy DAG • Deterministic Planner • Execution Monitor       │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────▼────────────────────────────────────┐  │
│  │               5. EXPERIENCE LEARNING SUBSYSTEM                        │  │
│  │  Append-Only History • Pattern Library • Confidence Calibrator        │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────▼────────────────────────────────────┐  │
│  │             6. BEHAVIOUR INTELLIGENCE PLATFORM                        │  │
│  │  Routine Learning • Drift Monitor • Caregiver Insights                │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────▼────────────────────────────────────┐  │
│  │             7. TRUST, SAFETY & CLINICAL LAYER                         │  │
│  │  6 Safety Guardrails • Care Policy • PII Audit Framework               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Standardized Subsystem Lifecycle

All core engines implement the `ICognitiveSubsystem` abstract base interface (`src/core/interfaces.py`):

```python
class ICognitiveSubsystem(ABC):
    def initialize(self) -> bool: ...
    def shutdown(self) -> bool: ...
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]: ...
    def status(self) -> str: ...
    def health(self) -> Dict[str, Any]: ...
    def metrics(self) -> Dict[str, Any]: ...
    def explain(self) -> str: ...
```

---

## 3. Data Flow & Event Pipeline

Single-pass non-blocking pipeline execution cycle:
1. `PerceptionManager`: Image capture, face recognition, object tracking.
2. `ContextFusionEngine`: Spatial, temporal, social context fusion.
3. `CognitiveKernel` (Phase 21): Working memory TTL expiration, attention focus update.
4. `BehaviourManager` (Phase 23): Routine learning, drift monitoring.
5. `CognitiveReasoningEngine` (Phase 24): Blackboard observation ingestion, conflict resolution, state estimation.
6. `ExecutiveEngine` (Phase 25): Goal ranking, deterministic task graph planning, divergence monitoring.
7. `ExperienceEngine` (Phase 26): Append-only history recording, confidence calibration.
8. `SafetyManager` (Phase 22): 6 Guardrails check (quiet hours, confidence thresholds, reminder throttling).
9. `CognitiveStream`: WebSockets streaming of consolidated payload to dashboard.
