# ADR-032: Cognitive Integrity & Consistency Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Architectural Integrity Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Ecosystem Integrity Architecture (Phase 32)

---

## 1. Problem Statement

Prior to Phase 32, MEMORA possessed ten deterministic cognitive subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session). Each subsystem was internally verified and tested. However, no subsystem continuously verified the cross-subsystem coherence, reference integrity, and structural health of the *entire* cognitive ecosystem.

Without a dedicated Integrity subsystem, broken references (e.g. Memory records referencing non-existent Knowledge facts or Executive goals referencing expired Memory IDs) could persist undetected across long-running operational deployments.

---

## 2. Design Goals

1. **Zero State Mutation & Zero Repair**: The framework acts purely as an architectural "immune system" that detects, classifies, explains, and reports integrity issues. It NEVER modifies cognitive states or auto-heals repositories.
2. **Deterministic & Lightweight**: Pure Python execution without external dependencies, ML models, neural networks, or background threads.
3. **Cross-Subsystem Coherence**: Validates reference integrity across Knowledge, Memory, Executive, Session, Trust, and Pipeline ordering contracts.
4. **Pure Read-Only Façade**: `IntegrityEngine` exposes `run_integrity_check()` which returns a comprehensive, deterministic `IntegrityReport`.

---

## 3. Alternative Designs Considered

### Alternative A: Active Auto-Healing & Self-Repair Engine
- **Overview**: Automatically rewrite memory records or delete orphaned knowledge references upon detection.
- **Advantages**: Solves inconsistency immediately without human intervention.
- **Disadvantages**: Non-auditable side effects, risk of silent data corruption, potential clinical policy violations.
- **Rejection Rationale**: Completely unacceptable for clinical dementia care where data mutation must remain transparent and auditable.

### Alternative B: Background Integrity Monitoring Thread
- **Overview**: Run a background daemon thread continuously scanning repositories.
- **Advantages**: Continuous real-time detection.
- **Disadvantages**: Thread contention overhead, non-deterministic timing, race conditions during active pipeline cycles.
- **Rejection Rationale**: Violates strict determinism and zero-thread-overhead design constraints.

---

## 4. Final Architecture

The selected design introduces a **Centralized Read-Only Cognitive Integrity Framework** (`src/integrity/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             COGNITIVE INTEGRITY & CONSISTENCY FRAMEWORK (PHASE 32)          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        INTEGRITY ENGINE                               │  │
│  │  • Read-Only Public Façade                                            │  │
│  │  • Coordinates IntegrityValidator & ConsistencyChecker                │  │
│  │  • Generates Unified IntegrityReport & Deterministic Explanations     │  │
│  └────────┬───────────────────────────────────┬──────────────────────────┘  │
│           │                                   │                             │
│  ┌────────▼────────────────────────┐  ┌───────▼──────────────────────────┐  │
│  │ IntegrityValidator              │  │ ConsistencyChecker               │  │
│  │ • Subsystem Registrations       │  │ • Memory <-> Knowledge Integrity │  │
│  │ • Interface Compliance          │  │ • Executive <-> Memory Integrity │  │
│  │ • Pipeline Contract Boundaries  │  │ • Session Reference Integrity    │  │
│  └─────────────────────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: ~504 production LOC across 6 modules in `src/integrity/`.
- **Public Interface**: `IntegrityEngine.run_integrity_check()`, `IntegrityExplainer.explain_report()`.

---

## 5. ADR Summary

**Decision**: Implement a pure read-only, non-mutating Cognitive Integrity & Consistency Framework (`src/integrity/`) that validates subsystem availability, interface compliance, pipeline stage ordering, and cross-subsystem reference integrity — achieving 100% test coverage with 387 total repository tests passing.
