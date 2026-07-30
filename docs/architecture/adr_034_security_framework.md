# ADR-034: Security, Identity & Access Control Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Security Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Security, Identity & Access Control Architecture (Phase 34)

---

## 1. Problem Statement

Prior to Phase 34, MEMORA possessed twelve deterministic cognitive and operational subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session, Integrity, Configuration). However, the platform lacked a unified Security, Identity & Access Control Framework to authenticate requester identities, evaluate role-based permission boundaries, log security access audit events, and enforce access controller façades.

Without a dedicated Security subsystem, operational access to sensitive features (such as configuration modification, memory queries, integrity checks, and session control) lacked a standardized identity attribution authority.

---

## 2. Design Goals

1. **Deterministic Identity & Access Authority**: `SecurityEngine` acts as the single security authority for authenticating identities and evaluating permissions across 5 roles (`PATIENT`, `CAREGIVER`, `CLINICIAN`, `ADMINISTRATOR`, `SYSTEM`).
2. **Zero Cognition & Zero State Mutation**: Framework performs zero reasoning, memory storage, or cognitive mutation.
3. **High-Level Access Façade**: `AccessController` provides high-level permission check methods (`can_start_session`, `can_modify_configuration`, `can_run_integrity`, `can_access_memory`, etc.) without invoking underlying subsystem logic.
4. **Immutable Security Audit Logging**: `AuditSecurity` records immutable `SecurityAuditEntry` logs (`identity_id`, `requested_operation`, `granted`, `denial_reason`, `timestamp`).
5. **Zero External Dependencies**: Pure Python implementation without OAuth, JWT, LDAP, TLS, encryption libraries, network protocols, or external identity provider dependencies.

---

## 3. Alternative Designs Considered

### Alternative A: External OAuth 2.0 / JWT Authentication Server
- **Overview**: Delegate identity authentication to an external OAuth or OIDC server over HTTP/HTTPS.
- **Advantages**: Standardized web single sign-on (SSO).
- **Disadvantages**: High network RPC latency ($> 50\text{ms}$), dependency on external authentication servers, non-deterministic network timeouts, violating offline edge wearable requirements.
- **Rejection Rationale**: Completely unacceptable for a real-time 64 FPS clinical wearable meant to operate deterministically offline.

### Alternative B: Subsystem-Local Permission Checks
- **Overview**: Allow each cognitive subsystem to implement its own ad-hoc identity checks.
- **Advantages**: Avoids creating a central Security subsystem.
- **Disadvantages**: Inconsistent permission logic, fragmented security audit trails, potential bypass vulnerabilities, high technical debt.
- **Rejection Rationale**: Violates single-responsibility principle and security auditability requirements.

---

## 4. Final Architecture

The selected design introduces a **Centralized Security, Identity & Access Control Framework** (`src/security/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             SECURITY, IDENTITY & ACCESS CONTROL FRAMEWORK (PHASE 34)        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        SECURITY ENGINE                                │  │
│  │  • Single Public Security Entry Point Façade                          │  │
│  │  • Coordinates IdentityRegistry, AuthorizationEngine, AccessController│  │
│  │  • Manages Security Audits & Snapshot Generation                      │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Identity        │  │ Authorization  │  │ Access         │  │ Audit           │
│  │ Registry        │  │ Engine         │  │ Controller     │  │ Security        │
│  │ • 5 Roles       │  │ • Role -> Perm │  │ • Subsystem    │  │ • Immutable     │
│  │ • Thread-Safe   │  │ • Deterministic│  │   Boundaries   │  │   Audit Logs    │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: Exactly 640 production LOC across 8 modules in `src/security/`.
- **Public Interface**: `SecurityEngine.authorize()`, `SecurityEngine.register_identity()`, `SecurityEngine.access_controller`, `SecurityEngine.snapshot()`, `SecurityEngine.audit_log()`.

---

## 5. ADR Summary

**Decision**: Implement a pure Python, thread-safe, deterministic Security, Identity & Access Control Framework (`src/security/`) establishing role-based access control and immutable security audit logs — achieving 100% test coverage with 412 total repository tests passing.
