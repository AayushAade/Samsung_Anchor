# ADR-029: Long-Term Memory Consolidation & Cognitive Recall Framework

- **Status**: Accepted & Certified
- **Deciders**: Principal Memory Architecture Board
- **Date**: 2026-07-30
- **Technical Scope**: MEMORA Cognitive Assistant Architecture (Phase 29)

---

## 1. Problem Statement

Prior to Phase 29, MEMORA possessed short-term working memory (`src/cognition/cos/working_memory.py`), semantic world facts (`src/knowledge/`), and execution logs (`src/experience/`), but lacked a unified **Long-Term Memory Consolidation Framework** responsible for memory record encoding, deduplicating, multi-indexing, deterministic recall, context reconstruction, retention policy management, and audit-trailed archiving.

Without long-term memory consolidation, cognitive context fragments could become redundant or lack structured retention expiration rules.

---

## 2. Design Goals

1. **Strict Determinism**: Zero neural networks, vector embedding similarity searches, or probabilistic memory decay. Every recall, index lookup, and retention evaluation follows explicit, reproducible rules.
2. **Exclusive Memory Ownership**: Memory owns long-term cognitive records (`MemoryRecord`). Semantic Knowledge (`src/knowledge/`) owns world facts. Experience (`src/experience/`) owns execution history.
3. **Synchronized Multi-Indexing**: Automatically maintain synchronized indexes across entity, category, location, routine, and importance dimensions.
4. **Audit-Trailed Archiving over Deletion**: Expired memories are archived according to retention policy (`CLINICAL` = never expire, `TEMPORARY` = 30 days, `DIAGNOSTIC` = 7 days) while preserving 100% recoverability.
5. **Context Reconstruction & Associative Networks**: Support step-by-step context reconstruction and explainable memory associations (Glasses $\rightarrow$ Patient $\rightarrow$ Bedroom $\rightarrow$ Morning Routine).

---

## 3. Alternative Designs Considered

### Alternative A: Neural Vector Embeddings & Vector Search (RAG)
- **Overview**: Store memory text as vector embeddings and recall via cosine similarity.
- **Advantages**: Flexible semantic similarity matching.
- **Disadvantages**: Non-deterministic search results, unexplainable distance scores, vector database overhead, potential retrieval hallucinations, zero clinical auditability.
- **Rejection Rationale**: Completely unacceptable for a clinical dementia care wearable where every decision must be reproducible and safety-guaranteed.

### Alternative B: Direct State Mutation of Working Memory
- **Overview**: Allow working memory to grow boundlessly over long-term operation.
- **Advantages**: Avoids creating a separate memory consolidation subsystem.
- **Disadvantages**: Working memory slots exceed TTL bounds, degrades pipeline latency, violates single-responsibility principle.
- **Rejection Rationale**: Unacceptable latency and architectural drift.

---

## 4. Final Architecture

The selected design introduces a **Centralized Long-Term Memory Consolidation Subsystem** (`src/memory/`) unifying cognitive memory encoding, deduplication, multi-indexing, recall, context reconstruction, and retention management:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             LONG-TERM MEMORY CONSOLIDATION SUBSYSTEM (PHASE 29)             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        MEMORY ENGINE                                  │  │
│  │  • Encodes Observations, Experiences & Knowledge into MemoryRecords    │  │
│  │  • Coordinates Deterministic Consolidation & Multi-Indexing           │  │
│  │  • Executes Exact, Associative & Context-Reconstructing Recall        │  │
│  └────────┬───────────────────┬───────────────────┬──────────────────────┘  │
│           │                   │                   │                         │
│  ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐  ┌─────────────▼───┐
│  │ Memory          │  │ Memory         │  │ Multi-Index    │  │ Associative     │
│  │ Encoder         │  │ Consolidator   │  │ Registry       │  │ Memory Engine   │
│  │ • Uniform       │  │ • Deduplication│  │ • Chronological│  │ • Entity-Room   │
│  │   Records       │  │ • Versioning   │  │ • Entity/Loc   │  │   Association   │
│  └─────────────────┘  └────────────────┘  └────────────────┘  └─────────────────┘
│           │                   │                   │                         │
│  ┌────────▼───────────────────▼───────────────────▼─────────────────────────┐
│  │ Retention & Forgetting Managers + Context Reconstructor + Explainer      │
│  │ • Retention Rules   • Recoverable Archiving   • Narrative Reconstruction │
│  └──────────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Layer Placement**: Step 6.55 of `CognitivePipeline.process()`.
- **Public Interfaces**: `MemoryEngine.process_cycle()`, `MemoryRecallEngine.recall_by_keyword()`, `ContextReconstructor.reconstruct_context()`, `MemoryValidator.validate_repository()`.

---

## 5. ADR Summary

**Decision**: Implement a deterministic, thread-safe Long-Term Memory Consolidation subsystem (`src/memory/`) operating between COS Working Memory and Behaviour Intelligence. The subsystem provides memory encoding, deduplicating consolidation, multi-indexing, deterministic recall, context reconstruction, associative networks, retention policy management, and audit-trailed archiving — achieving complete long-term cognitive memory management with 100% test coverage and zero non-deterministic algorithms.
