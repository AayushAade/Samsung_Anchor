# ADR-031: Cognitive Session Framework

- **Status**: Accepted
- **Date**: 2026-07-30
- **Scope**: MEMORA Cognitive Session Architecture (Phase 31)

---

## 1. Problem Statement

MEMORA's cognitive pipeline processes inputs through 13+ subsystems per cycle but lacks a first-class abstraction for one complete user interaction. Without a session concept, there is no unified lifecycle record connecting perception to response, making replay, debugging, and auditability harder than necessary.

## 2. Design Goals

1. **Minimal footprint**: 5 files, ~300 lines of non-test code total.
2. **Zero cognitive logic**: The session layer orchestrates; it does not reason.
3. **Composition over inheritance**: `SessionEngine` composes `SessionManager`; neither extends `CognitivePipeline`.
4. **Reference-only context**: `SessionContext` holds pointers, never copies.
5. **Full backwards compatibility**: `pipeline.process()` works identically with or without sessions.

## 3. Alternatives Considered

| Alternative | Why Rejected |
| :--- | :--- |
| Embed session tracking inside `CognitivePipeline.process()` | Violates single-responsibility; couples session logic to pipeline internals |
| Make `CognitiveSession` an `ICognitiveSubsystem` | Sessions are not subsystems — they are execution envelopes |
| Introduce a session database | Premature; in-memory tracking is sufficient for the current runtime |

## 4. Architecture

```
SessionEngine.execute(pipeline, input)
    │
    ├── SessionManager.create_session()
    ├── SessionManager.transition(RUNNING)
    │
    ├── pipeline.process(input)          ← existing pipeline, unchanged
    │
    ├── SessionManager.record_subsystem() × N
    ├── SessionManager.record_trace_step()
    ├── SessionManager.complete_session()
    │
    └── SessionExplainer.explain()       ← Markdown summary
```

The `SessionEngine` wraps the pipeline as an outer orchestration layer. The pipeline itself is unmodified.

## 5. Module Inventory

| File | Lines | Responsibility |
| :--- | :--- | :--- |
| `session_models.py` | ~65 | `CognitiveSession`, `SessionState`, `SessionTransition` |
| `session_context.py` | ~42 | `SessionContext` — lightweight reference container |
| `session_manager.py` | ~110 | CRUD, state transitions, trace recording |
| `session_explainer.py` | ~55 | Markdown summary generation |
| `session_engine.py` | ~105 | Orchestration wrapper around pipeline |

**Total non-test code**: ~377 lines across 5 files. This is deliberately minimal.
