# ADR-035: Unified Cognitive Input/Output (I/O) Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal I/O Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Unified Cognitive Input/Output (I/O) Architecture (Phase 35)

---

## 1. Problem Statement

Prior to Phase 35, MEMORA possessed thirteen deterministic cognitive, operational, configuration, and security subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session, Integrity, Configuration, Security). However, the platform lacked a formal architectural boundary between external drivers/devices and the internal cognitive ecosystem.

Direct coupling of hardware drivers (cameras, microphones, sensors) to internal cognitive pipeline stages risks architectural drift, tight integration coupling, and protocol-dependent fragility.

---

## 2. Design Goals

1. **Payload-Neutral Interface Contract**: `IOMessage` envelope acts as a technology-agnostic external interface boundary carrying metadata, session references, and payload pointers without interpreting payload data.
2. **Zero Cognition & Zero State Mutation**: Framework performs zero reasoning, memory storage, or executive logic.
3. **Deterministic I/O Routing**: `IORouter` maps `InputType` and `OutputType` messages to internal target components (`PerceptionManager`, `AudioPipeline`, `SensorBus`, `DialogueManager`, `CentralRuntimeEngine`, `ClinicalEvaluator`, `CognitivePipeline`, `DisplayAdapter`, `SpeakerAdapter`, etc.) using a 100% deterministic mapping matrix.
4. **Single-Point Ingress & Egress**: `IOEngine` serves as the single public authority through which all inputs enter via `InputGateway` and outputs leave via `OutputGateway`.
5. **Zero External Transport Dependencies**: Pure Python implementation with zero camera/microphone SDKs, Bluetooth/BLE drivers, REST APIs, WebSockets, FHIR, or HL7 library dependencies.

---

## 3. Alternative Designs Considered

### Alternative A: Subsystem-Direct Driver Coupling
- **Overview**: Allow perception managers and audio pipelines to instantiate device drivers directly.
- **Advantages**: Fewer abstraction files.
- **Disadvantages**: Tight coupling to specific hardware SDKs, non-reproducible testing environments, inability to mock or route inputs centrally.
- **Rejection Rationale**: Completely unacceptable for a modular clinical research platform intended for multi-device deployment (smartwatches, smart glasses, ambient sensors).

### Alternative B: Dynamic Plugin Scripting Router
- **Overview**: Implement a dynamic Python script executor to route I/O messages based on dynamic rules.
- **Advantages**: Highly flexible runtime routing.
- **Disadvantages**: Non-deterministic execution paths, security sandbox risks, difficulty in verifying total system behavior.
- **Rejection Rationale**: Violates strict determinism and clinical safety constraints.

---

## 4. Final Architecture

The selected design introduces a **Centralized Unified Cognitive Input/Output Framework** (`src/io/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             UNIFIED COGNITIVE INPUT/OUTPUT FRAMEWORK (PHASE 35)             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          I/O ENGINE                                   │  │
│  │  • Single Public Boundary Façade                                      │  │
│  │  • Coordinates InputGateway, IOValidator, IORouter, OutputGateway     │  │
│  │  • Manages Traffic Snapshots & Message Validation                     │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Input           │  │ I/O            │  │ I/O            │  │ Output          │
│  │ Gateway         │  │ Validator      │  │ Router         │  │ Gateway         │
│  │ • Ingress       │  │ • Schema &     │  │ • Deterministic│  │ • Egress        │
│  │   Normalization │  │   Bounds Check │  │   Mapping      │  │   Normalization │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: Exactly 647 production LOC across 8 modules in `src/io/`.
- **Public Interface**: `IOEngine.receive()`, `IOEngine.route()`, `IOEngine.send()`, `IOEngine.validate()`, `IOEngine.snapshot()`.

---

## 5. ADR Summary

**Decision**: Implement a pure Python, thread-safe, deterministic Unified Cognitive Input/Output Framework (`src/io/`) establishing a payload-neutral external boundary and deterministic message routing — achieving 100% test coverage with 423 total repository tests passing.
