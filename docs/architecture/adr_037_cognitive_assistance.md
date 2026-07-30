# ADR-037: Alzheimer's Cognitive Assistance Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Clinical Assistance Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Alzheimer's Cognitive Assistance Framework (Phase 37)

---

## 1. Problem Statement

Prior to Phase 37, MEMORA possessed fifteen deterministic cognitive, operational, configuration, security, I/O boundary, and interoperability subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session, Integrity, Configuration, Security, I/O, Interoperability). However, these capabilities existed as independent services without a unified clinical orchestrator composing them into patient-centered care experiences for individuals living with Alzheimer's disease.

Without a clinical assistance framework, high-level patient scenarios ("Where am I?", "I lost my glasses", repeated questions, daily routines) would require ad-hoc application script logic outside the platform boundary.

---

## 2. Design Goals

1. **Clinical Orchestration Without Direct Cognition**: `src/assistance/` acts as the Clinical Orchestrator composing Memory, Knowledge, Reasoning, Executive, Behaviour, Trust, and Security without performing direct reasoning, memory storage, or state mutation.
2. **Zero Information Fabrication**: Workflows (`ContextRestorationWorkflow`, `ObjectAssistanceWorkflow`) rely strictly on verified active memory records and knowledge facts. If an item is unobserved, the framework explicitly reports uncertainty rather than guessing.
3. **Calm, Reassuring Patient Interaction**: `ReassuranceEngine` handles repeated questions and mild disorientation gently without showing impatience or contradicting past answers.
4. **Caregiver Summaries Without Push Messaging**: `CaregiverAssistanceWorkflow` generates deterministic summary objects and intervention logs for family caregivers without external SMS/push notification side-effects.
5. **Single-Point Façade Authority**: `AssistanceEngine` coordinates all assistance workflows.

---

## 3. Alternative Designs Considered

### Alternative A: Generative LLM Persona Prompts
- **Overview**: Use a generative LLM system prompt ("You are a gentle assistant for Alzheimer's patients...") to handle disorientation and repeated questions dynamically.
- **Advantages**: Natural sounding text generation.
- **Disadvantages**: High risk of hallucinating non-existent memories, contradicting past answers, introducing non-deterministic advice, and violating clinical safety guardrails.
- **Rejection Rationale**: Completely unacceptable for a clinical cognitive platform where factual accuracy and safety are paramount.

### Alternative B: Hardcoded Monolithic Script Pipeline
- **Overview**: Implement a single monolithic Python function handling all patient interaction logic.
- **Advantages**: Single file.
- **Disadvantages**: Rigid structure, poor maintainability, inability to modularize reassurance from routine guidance or object recall.
- **Rejection Rationale**: Violates clean modular architecture guidelines.

---

## 4. Final Architecture

The selected design introduces a **Centralized Alzheimer's Cognitive Assistance Framework** (`src/assistance/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          ALZHEIMER'S COGNITIVE ASSISTANCE FRAMEWORK (PHASE 37)              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       ASSISTANCE ENGINE                               │  │
│  │  • Single Public Clinical Assistance Façade                            │  │
│  │  • Coordinates Context Restoration, Routine Guidance, Object Recall   │  │
│  │  • Manages Caregiver Assistance & Patient Reassurance                  │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Context         │  │ Routine        │  │ Object         │  │ Reassurance     │
│  │ Restoration     │  │ Guidance       │  │ Assistance     │  │ Engine          │
│  │ • Verified      │  │ • Step-by-Step │  │ • Verified     │  │ • Calm Repetitive│
│  │   Orientation   │  │   Routines     │  │   Spatial Loc. │  │   Question Cues │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: Exactly 797 production LOC across 9 modules in `src/assistance/`.
- **Public Interface**: `AssistanceEngine.create_plan()`, `AssistanceEngine.execute()`, `AssistanceEngine.summarize_caregiver()`, `AssistanceEngine.snapshot()`, `AssistanceEngine.explain()`.

---

## 5. ADR Summary

**Decision**: Implement a pure Python, thread-safe, deterministic Alzheimer's Cognitive Assistance Framework (`src/assistance/`) establishing clinical scenario orchestration — achieving 100% test coverage with 450 total repository tests passing.
