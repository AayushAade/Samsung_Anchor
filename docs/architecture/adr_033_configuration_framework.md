# ADR-033: Unified Configuration & Policy Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Configuration Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Unified Configuration & Policy Architecture (Phase 33)

---

## 1. Problem Statement

Prior to Phase 33, MEMORA possessed eleven deterministic cognitive and operational subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session, Integrity). However, runtime parameters, safety thresholds, memory limits, reasoning confidence floors, and deployment-specific settings existed as distributed constants or subsystem-local configs.

Without a centralized Configuration & Policy Framework, subsystem settings could drift across environments or become inconsistent without a single, deterministic source of truth.

---

## 2. Design Goals

1. **Single Source of Truth**: `ConfigurationEngine` acts as the unified, thread-safe entry point for accessing parameters and evaluating policies across all 8 scopes (`SYSTEM`, `COGNITIVE`, `TRUST`, `MEMORY`, `REASONING`, `EXECUTIVE`, `RUNTIME`, `SESSION`).
2. **Zero Cognition & Zero State Mutation**: Framework owns configuration, policy definitions, validation, and runtime access ONLY. It NEVER performs reasoning, stores memories, or modifies cognitive state.
3. **Deterministic Deployment Profiles**: Inherited profiles (`DEVELOPMENT`, `TESTING`, `SIMULATION`, `CLINICAL_DEMO`, `PRODUCTION`) override defaults deterministically.
4. **Registry Freezing**: Supports locking registry state via `freeze()` to prevent unauthorized runtime parameter mutation during production deployment.
5. **Zero External Dependencies**: Pure Python implementation with zero YAML/JSON file parsers, env-var parsers, network reloaders, or background threads.

---

## 3. Alternative Designs Considered

### Alternative A: YAML/JSON File Parsing & Environment Variable Overrides
- **Overview**: Read configuration from external `.yaml` files or system environment variables at runtime.
- **Advantages**: Easy for external devops tooling.
- **Disadvantages**: Non-deterministic file parsing risks, env-var pollution, file-not-found exceptions, potential runtime injection vulnerabilities.
- **Rejection Rationale**: Completely unacceptable for a clinical wearable where configuration state must be 100% deterministic, self-contained, and code-auditable.

### Alternative B: Auto-Reloading File Watcher Thread
- **Overview**: Spawn a background file watcher thread to reload settings dynamically when files change.
- **Advantages**: Live updates without restarting process.
- **Disadvantages**: Thread contention, race conditions during mid-pipeline cycles, non-deterministic state changes.
- **Rejection Rationale**: Violates strict determinism and zero-thread-overhead design constraints.

---

## 4. Final Architecture

The selected design introduces a **Centralized Unified Configuration & Policy Framework** (`src/configuration/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             UNIFIED CONFIGURATION & POLICY FRAMEWORK (PHASE 33)             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     CONFIGURATION ENGINE                              │  │
│  │  • Single Public Entry Point Façade                                   │  │
│  │  • Coordinates ConfigurationRegistry, PolicyRegistry, Validator       │  │
│  │  • Manages Deployment Profiles & Registry Freezing                     │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Configuration   │  │ Policy         │  │ Configuration  │  │ Configuration   │
│  │ Registry        │  │ Registry       │  │ Validator      │  │ Explainer       │
│  │ • 8 Scopes      │  │ • 7 Types      │  │ • Range & Bound│  │ • Deterministic │
│  │ • Thread-Safe   │  │ • Structured   │  │   Checks       │  │   Markdown Log  │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: Exactly 710 production LOC across 7 modules in `src/configuration/`.
- **Public Interface**: `ConfigurationEngine.get_configuration()`, `ConfigurationEngine.evaluate_policy()`, `ConfigurationEngine.set_profile()`, `ConfigurationEngine.freeze()`, `ConfigurationEngine.validate()`.

---

## 5. ADR Summary

**Decision**: Implement a pure Python, thread-safe, freezable Unified Configuration & Policy Framework (`src/configuration/`) providing single-source-of-truth access to all platform settings and structured policy rules — achieving 100% test coverage with 399 total repository tests passing.
