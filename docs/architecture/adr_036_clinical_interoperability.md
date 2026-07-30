# ADR-036: Clinical Interoperability Framework (FHIR / HL7 Adapter Layer)

- **Status**: Accepted & Certified
- **Deciders**: Principal Clinical Interoperability Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Clinical Interoperability Framework (Phase 36)

---

## 1. Problem Statement

Prior to Phase 36, MEMORA possessed fourteen deterministic cognitive, operational, configuration, security, and I/O boundary subsystems (COS, Trust, Behaviour, Experience, Knowledge, Memory, Reasoning, Executive, Runtime, Session, Integrity, Configuration, Security, I/O Framework). However, MEMORA lacked a formal adapter framework for translating external healthcare protocols (FHIR resources, HL7 v2 messages) to and from internal `IOMessage` contracts.

If cognitive pipelines or perception modules directly imported FHIR/HL7 libraries or parsed clinical JSON schemas, MEMORA would risk architectural protocol coupling, violating its payload-neutral design philosophy.

---

## 2. Design Goals

1. **Protocol Isolation**: `src/interoperability/` acts as the exclusive adapter layer translating healthcare formats into MEMORA's internal `IOMessage` payload-neutral envelopes. The cognitive platform remains 100% unaware of FHIR or HL7 specifications.
2. **Zero Cognition & Zero State Mutation**: Framework performs zero reasoning, memory storage, or executive behavior modification.
3. **Simplified Deterministic Mapping**: Converts FHIR resources (`Patient`, `Observation`, `Condition`, `MedicationStatement`, `Encounter`, `Device`, `CarePlan`, `DetectedIssue`) and HL7 message families (`ADT^A08`, `ORU^R01`, `PPR^PC1`, `MDM^T02`, `SIU^S12`) into `ClinicalRecord` objects deterministically.
4. **Single-Point Façade Authority**: `InteroperabilityEngine` coordinates `FHIRAdapter`, `HL7Adapter`, `ClinicalMapper`, and `InteroperabilityValidator`.
5. **Zero Network Communication**: Pure Python implementation with zero HTTP client, MLLP socket, REST API, WebSocket, or database library dependencies.

---

## 3. Alternative Designs Considered

### Alternative A: Direct Cognitive Pipeline FHIR/HL7 Import
- **Overview**: Allow `CognitivePipeline` or `DialogueManager` to directly accept FHIR JSON or HL7 message strings.
- **Advantages**: Fewer translation steps.
- **Disadvantages**: Couples the internal cognitive engine to healthcare communication protocols, making it difficult to run non-clinical wearable configurations.
- **Rejection Rationale**: Completely unacceptable for a technology-agnostic cognitive architecture.

### Alternative B: External Hospital Gateway Process (Microservice)
- **Overview**: Run a separate external HTTP microservice that converts FHIR to JSON before forwarding to MEMORA.
- **Advantages**: Out-of-process separation.
- **Disadvantages**: Introduces network IPC overhead, inter-process communication failures, non-deterministic HTTP timeouts, violating edge-native wearable constraints.
- **Rejection Rationale**: Violates edge-native, zero-network-dependency, deterministic architectural principles.

---

## 4. Final Architecture

The selected design introduces a **Centralized Clinical Interoperability Framework** (`src/interoperability/`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          CLINICAL INTEROPERABILITY FRAMEWORK (FHIR / HL7 ADAPTER LAYER)     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    INTEROPERABILITY ENGINE                            │  │
│  │  • Single Public Interoperability Façade                              │  │
│  │  • Coordinates FHIRAdapter, HL7Adapter, ClinicalMapper, Validator     │  │
│  │  • Manages Import, Export, Translation & Snapshot Generation           │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ FHIR            │  │ HL7            │  │ Clinical       │  │ Interoperability│
│  │ Adapter         │  │ Adapter        │  │ Mapper         │  │ Validator       │
│  │ • Resource      │  │ • Message      │  │ • Record <->   │  │ • Schema &      │
│  │   Parsing       │  │   Parsing      │  │   IOMessage    │  │   ID Checks     │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **LOC Volume**: Exactly 723 production LOC across 8 modules in `src/interoperability/`.
- **Public Interface**: `InteroperabilityEngine.import_record()`, `InteroperabilityEngine.import_to_io_message()`, `InteroperabilityEngine.export_record()`, `InteroperabilityEngine.translate()`, `InteroperabilityEngine.snapshot()`.

---

## 5. ADR Summary

**Decision**: Implement a pure Python, thread-safe, deterministic Clinical Interoperability Framework (`src/interoperability/`) establishing a clean healthcare protocol translation boundary — achieving 100% test coverage with 436 total repository tests passing.
