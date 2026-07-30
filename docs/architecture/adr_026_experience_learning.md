# ADR-026: Experience Learning & Adaptive Knowledge Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Architecture Review Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Cognitive Assistant Architecture (Phase 26)

---

## 1. Problem Statement

Prior to Phase 26, MEMORA possessed deterministic executive planning (Phase 25) capable of generating hierarchical goal task graphs and managing reality divergence. However, the system lacked a persistent **Experience Learning Framework** to accumulate completed plan execution histories, classify outcome successes/failures, derive empirical success metrics, extract reusable execution patterns, calibrate plan confidence, and optimize repetitive daily routines over time.

Without an Experience Layer, every planning cycle operated without historical memory of past execution performance, missing opportunities to improve routine assistance while forcing redundant plan synthesis.

---

## 2. Design Goals

1. **Strict Determinism**: Zero black-box neural networks, gradient optimization, or reinforcement learning. All pattern extraction and confidence calibration reliance must be 100% reproducible arithmetic aggregations.
2. **Append-Only History Persistence**: Execution records are stored persistently without modifying historical records (`ExperienceRepository`).
3. **Advisory Recommendation Interface**: The Experience subsystem provides recommendations to the Executive Planner (`src/executive/`). Planning authority remains exclusively with the Executive Engine.
4. **Transparent Failure Analysis**: Classify unsuccessful executions into structured root cause records (missing evidence, incorrect assumptions, sensor limitations, timeouts).
5. **Caregiver Preference Integration**: Maintain explicit, editable caregiver operational preferences without hidden inference.

---

## 3. Alternative Designs Considered

### Alternative A: Neural Network Policy Gradient Adaptation
- **Overview**: Train an online neural network to update executive planning probabilities based on execution feedback.
- **Advantages**: Potential to discover non-obvious correlations across high-dimensional feature spaces.
- **Disadvantages**: Opaque decision-making, catastrophic forgetting risks, impossible clinical auditability, non-deterministic outputs violating clinical safety.
- **Rejection Rationale**: Completely unacceptable for a clinical dementia care wearable where predictable, reproducible behaviour is legally and ethically required.

### Alternative B: Direct Executive Engine State Mutation
- **Overview**: Allow the Experience Engine to mutate Executive Goal parameters and task graphs directly during execution.
- **Advantages**: Avoids creating separate recommendation data structures between Experience and Executive modules.
- **Disadvantages**: Introduces tight coupling, potential race conditions, circular dependencies, and violates the single-responsibility principle.
- **Rejection Rationale**: Violates modular separation of concerns.

### Alternative C: Unstructured Text Log Parsing
- **Overview**: Parse standard application log files using regex to compute execution statistics.
- **Advantages**: No dedicated data models needed.
- **Disadvantages**: Fragile, slow, unindexed, incapable of supporting real-time $< 1\text{ms}$ executive queries.
- **Rejection Rationale**: Structurally unreliable for real-time cognitive operations.

---

## 4. Final Architecture

The selected design introduces a **Centralized Experience Learning Subsystem** (`src/experience/`) positioned as an additive layer between Cognitive Reasoning (Phase 24) and Behaviour Intelligence (Phase 23):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 EXPERIENCE LEARNING SUBSYSTEM (PHASE 26)                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       EXPERIENCE ENGINE                               │  │
│  │  • Receives Completed Execution Records & Environmental Context       │  │
│  │  • Append-only Persistence in Experience Repository                   │  │
│  │  • Classifies Outcomes & Computes Success Metrics                     │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Experience      │  │ Pattern        │  │ Failure        │  │ Confidence      │
│  │ Repository      │  │ Library        │  │ Analyzer       │  │ Calibrator      │
│  │ • Append-Only   │  │ • Reusable     │  │ • Root Cause   │  │ • Variance      │
│  │ • Context       │  │   Sequences    │  │ • Missing Ev.  │  │ • Rec. Score    │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
│           │                   │                   │                         │
│  ┌────────▼───────────────────▼───────────────────▼─────────────────────────┐
│  │         Routine Optimizer + Preference Manager + Experience Explainer      │
│  │  • Routine Statistics   • Caregiver Preferences   • Explanation Narrative │
│  └──────────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Layer Placement**: Step 6.9 of `CognitivePipeline.process()`.
- **Public Interfaces**: `ExperienceEngine.process_cycle()`, `PatternLibrary.find_recommended_pattern()`, `ConfidenceCalibrator.calibrate_confidence()`, `SuccessMetricsEngine.compute_metrics()`.
- **Data Flow**: `ExecutiveEngine` outputs $\rightarrow$ `ExperienceEngine` $\rightarrow$ `ExperienceRepository` $\rightarrow$ `PatternLibrary` $\rightarrow$ `ConfidenceCalibrator` $\rightarrow$ `CognitiveStream` & Dashboard.

---

## 5. Trade-Off Analysis

1. **Statistical Aggregation vs. Deep Learning**: Selected deterministic arithmetic aggregation over neural learning. Sacrifices implicit feature discovery in exchange for 100% auditable, predictable clinical safety.
2. **In-Memory Buffer vs. Disk I/O**: Retained in-memory append-only buffer bounded at 500 records to guarantee $< 1\text{ms}$ query latency during active 60 FPS pipeline execution.
3. **Advisory Recommendations vs. Direct Control**: Experience Engine provides recommendations ONLY; Executive Engine retains single authority over planning decisions.

---

## 6. Architectural Risks

1. **Repository Memory Bounds**: If execution records exceed capacity limits, older records are purged. Mitigated by `MAX_RECORDS = 500` ring buffer pruning and background database persistence.
2. **Sparse Data Cold Start**: Early execution cycles have minimal historical records. Mitigated by seeding baseline execution patterns (`PatternLibrary._seed_baseline_patterns()`).

---

## 7. Future Evolution

Phase 26 establishes a complete experience foundation enabling future enhancements without architectural redesign:
- **Cross-User Anonymized Analytics**: Export append-only execution records for clinical population research.
- **Retrieval-Augmented Planning**: Use vector similarity to retrieve past similar execution contexts.

---

## 8. Lessons Learned

- **Append-Only Integrity**: Guaranteeing that completed execution records are immutable simplified historical querying and eliminated state mutation bugs.
- **Separation of Recommendation and Authority**: Restricting Experience Engine to an advisory role preserved clean executive control boundaries.

---

## 9. ADR Summary

**Decision**: Implement a deterministic, append-only Experience Learning subsystem (`src/experience/`) operating between Cognitive Reasoning and Behaviour Intelligence. The subsystem provides historical execution logging, pattern extraction, outcome evaluation, failure root cause analysis, calibrated confidence recommendations, routine optimization, and caregiver preference management — achieving continuous planning improvement with 100% test coverage and zero non-deterministic algorithms.
