# ADR-030: Clinical Runtime, Observability & Deployment Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Operational Review Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Operational Runtime Architecture (Phase 30)

---

## 1. Problem Statement

Prior to Phase 30, MEMORA possessed rich cognitive intelligence layers across COS, Trust, Behaviour, Reasoning, Executive, Experience, Knowledge, and Memory, but lacked a production-grade **Clinical Runtime, Observability, and Deployment Infrastructure** to manage operational lifecycles, structured JSON logging, distributed execution tracing, fault isolation boundaries, deterministic recovery workflows, versioned configuration profiles, and system-wide health diagnostics.

Without a dedicated Runtime subsystem, errors in one cognitive module risked cascading across the pipeline or resulting in unexplainable operational failures.

---

## 2. Design Goals

1. **Operational Infrastructure Only**: Zero changes to cognitive logic or subsystem boundaries. The Runtime Engine manages operational lifecycle only.
2. **Fault Isolation Boundaries**: Subsystem exceptions are isolated (`FaultManager`) to prevent full platform crashes, supporting graceful degradation.
3. **Deterministic Recovery Workflows**: Execute auditable, deterministic recovery actions (`RESTART_SERVICE`, `REBUILD_CACHES`, `RESTORE_STATE`, `RELOAD_CONFIG`).
4. **Versioned Runtime Profiles**: Traceable configuration profiles (`DEVELOPMENT`, `SIMULATION`, `CLINICAL_DEMO`, `PRODUCTION`).
5. **Structured Logging & Tracing**: JSON structured logs and end-to-end distributed execution trace explanations across all pipeline stages.

---

## 3. Alternative Designs Considered

### Alternative A: Monolithic Try-Catch Pipeline Wrapping
- **Overview**: Wrap the entire cognitive pipeline in a single top-level `try-except` block.
- **Advantages**: Minimal code changes required.
- **Disadvantages**: Lack of fault isolation, coarse-grained error reporting, zero subsystem recoverability, loss of clinical explainability.
- **Rejection Rationale**: Completely unacceptable for a clinical wearable where individual subsystem health must be isolated and monitored.

### Alternative B: External Microservice Container Isolation
- **Overview**: Deploy each cognitive layer as a separate Docker container communicating via RPC.
- **Advantages**: Maximum process isolation.
- **Disadvantages**: Severe RPC network latency overhead ($> 20\text{ms}$ per hop), violating real-time 60 FPS wearable requirements.
- **Rejection Rationale**: Violates latency budget constraints.

---

## 4. Final Architecture

The selected design introduces a **Centralized Clinical Runtime & Observability Subsystem** (`src/runtime/`) operating as the sole owner of operational lifecycle management:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             CLINICAL RUNTIME & OBSERVABILITY FRAMEWORK (PHASE 30)           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        RUNTIME ENGINE                                 │  │
│  │  • Orchestrates System Lifecycle, Service Registry & Scheduler        │  │
│  │  • Manages Structured JSON Logs & End-to-End Distributed Tracing      │  │
│  │  • Monitors System Health, Resource Usage & Operational Diagnostics   │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Runtime         │  │ Service        │  │ Fault          │  │ Recovery        │
│  │ Configuration   │  │ Registry       │  │ Manager        │  │ Orchestrator    │
│  │ • 4 Profiles    │  │ • Lifecycle    │  │ • Isolation    │  │ • Restart/Reload│
│  │ • Versioned     │  │ • Health       │  │ • Degradation  │  │ • State Restore │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
│           │                   │                   │                         │
│  ┌────────▼───────────────────▼───────────────────▼─────────────────────────┐
│  │   Runtime Scheduler + Metrics Aggregator + Explainer & Audit Framework   │
│  │ • Task Scheduler    • Resource Metrics    • Trace Explainer & Audit Logs │
│  └──────────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Layer Placement**: Operational wrapper executing at Step 0 and Step 9 of `CognitivePipeline.process()`.
- **Public Interfaces**: `CentralRuntimeEngine.process_cycle()`, `ServiceRegistry.get_health_status()`, `FaultManager.record_fault()`, `RecoveryOrchestrator.recover_subsystem()`.

---

## 5. ADR Summary

**Decision**: Implement a production-grade Clinical Runtime & Observability subsystem (`src/runtime/`) owning system lifecycles, versioned configuration profiles, fault isolation boundaries, deterministic recovery orchestrations, JSON structured logging, end-to-end distributed tracing, and system health reporting — achieving deployment readiness with 100% test coverage and zero changes to cognitive subsystem boundaries.
