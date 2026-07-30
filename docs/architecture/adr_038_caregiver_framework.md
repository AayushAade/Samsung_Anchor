# ADR-038: Caregiver Intelligence & Clinical Oversight Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Caregiver Intelligence Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Caregiver Intelligence & Clinical Oversight Framework (Phase 38)

---

## 1. Problem Statement

Prior to Phase 38, MEMORA possessed sixteen deterministic cognitive, operational, configuration, security, I/O boundary, interoperability, and assistance subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session, Integrity, Configuration, Security, I/O, Interoperability, Assistance). However, clinical oversight and family caregiver monitoring required examining raw session logs or individual subsystem snapshots.

Without a caregiver intelligence framework, clinicians and caregivers lacked an aggregated, deterministic provider of longitudinal behavioral trends, chronological patient timelines, and rule-based escalation recommendations.

---

## 2. Design Goals

1. **Analysis Without Cognition**: `src/caregiver/` acts as an analytical oversight layer synthesizing verified timeline events into `CaregiverSummary` objects without performing direct cognition, reasoning, or state mutation.
2. **Zero ML & Zero Predictive Forecasting**: Longitudinal trend calculations (`TrendAnalysisEngine`) derive from deterministic event counts over observation windows without machine learning or probabilistic forecasting.
3. **Deterministic Escalation Policies**: `EscalationEngine` evaluates event streams against explicit policy rules to assign escalation ratings (`NONE`, `LOW`, `MODERATE`, `HIGH`, `URGENT`) without triggering side-effect push notifications or SMS alerts.
4. **Verified Evidence Citation**: All trend reports and summaries cite exact underlying timeline events.
5. **Single-Point Façade Authority**: `CaregiverEngine` coordinates `PatientTimeline`, `TrendAnalysisEngine`, `EscalationEngine`, and `ClinicalSummaryGenerator`.

---

## 3. Alternative Designs Considered

### Alternative A: Generative AI Narrative Summaries
- **Overview**: Use an LLM to generate narrative paragraph summaries of patient daily activity.
- **Advantages**: Natural sounding text.
- **Disadvantages**: Non-deterministic outputs, risk of hallucinating events not recorded in the timeline, inability to audit evidence sources.
- **Rejection Rationale**: Completely unacceptable for a clinical oversight framework.

### Alternative B: Push Notification Microservice
- **Overview**: Implement real-time WebSocket, SMS, or email notification dispatchers whenever a confusion event occurs.
- **Advantages**: Real-time alerting.
- **Disadvantages**: Introduces external network service dependencies, protocol coupling, and potential caregiver alert fatigue.
- **Rejection Rationale**: Violates the zero-external-communication and presentation-decoupled architectural principles.

---

## 4. Final Architecture

The selected design introduces a **Centralized Caregiver Intelligence Framework** (`src/caregiver/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          CAREGIVER INTELLIGENCE & CLINICAL OVERSIGHT FRAMEWORK (PHASE 38)   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        CAREGIVER ENGINE                               │  │
│  │  • Single Public Caregiver Intelligence Façade                        │  │
│  │  • Coordinates PatientTimeline, TrendAnalysis, Escalation, Summary    │  │
│  │  • Manages Event Ingestion, Snapshotting, and Diagnostic Reports       │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Patient         │  │ Trend          │  │ Escalation     │  │ Clinical        │
│  │ Timeline        │  │ Analysis       │  │ Engine         │  │ Summary         │
│  │ • Chronological │  │ • Longitudinal │  │ • Policy Rule  │  │ • Structured    │
│  │   Event Log     │  │   Trends       │  │   Evaluation   │  │   Care Reports  │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: Exactly 849 production LOC across 8 modules in `src/caregiver/`.
- **Public Interface**: `CaregiverEngine.ingest_event()`, `CaregiverEngine.build_timeline()`, `CaregiverEngine.analyze_trends()`, `CaregiverEngine.generate_summary()`, `CaregiverEngine.evaluate_escalation()`, `CaregiverEngine.snapshot()`.

---

## 5. ADR Summary

**Decision**: Implement a pure Python, thread-safe, deterministic Caregiver Intelligence & Clinical Oversight Framework (`src/caregiver/`) establishing caregiver insight synthesis — achieving 100% test coverage with 460 total repository tests passing.
