# Memory Lead Engineering Handover & Implementation Roadmap

## 1. Current State of the Memory Module

### Current maturity
The Memory module is currently at a prototype-to-early-product maturity level. It is not a stub, and it is not a fully finished subsystem, but it is already functional enough to support real identity and object persistence flows.

### Current implementation status
The current implementation is concentrated in two files:

- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)

The Memory module currently provides:

- SQLite-backed persistence for identities
- embedding storage
- evidence accumulation
- object logging and history
- room-state persistence
- a basic spatial object tracker

### Current responsibilities
The current Memory subsystem is responsible for:

- storing and retrieving identity information,
- storing and comparing face embeddings,
- accumulating evidence and confidence for identities,
- storing object sightings and their history,
- storing the current room context,
- and supporting the current Vision integration path.

### Strengths
The strongest parts of the current Memory module are:

- it is backed by a real SQLite file, [memora_db.sqlite](memora_db.sqlite),
- it exposes concrete methods rather than relying on a purely abstract interface,
- it already supports basic identity lifecycle operations,
- it already stores object history and last-known locations,
- and it contains basic locking for concurrent access.

### Weaknesses
The current weaknesses are:

- the configuration layer is incomplete,
- the public API is still implementation-driven,
- the integration contract is not formalized,
- the object-tracking path is not fully integrated into the same runtime flow as the identity pipeline,
- and the Memory module is still heavily coupled to the current Vision assumptions.

### Dependencies
The Memory module currently depends on:

- [config/settings.py](config/settings.py) for runtime configuration values
- [src/vision/face_recognizer.py](src/vision/face_recognizer.py) for direct calls into the database layer
- [archive/week1/demo_week1.py](archive/week1/demo_week1.py) and [archive/week2/demo_week2.py](archive/week2/demo_week2.py) as historical integration examples
- the SQLite database file [memora_db.sqlite](memora_db.sqlite)

### Risk level
Medium. The Memory module is usable, but it is easy to break downstream behavior if the public API or schema semantics change in an incompatible way.

### Current integration status
The Memory module is integrated with:

- Vision identity matching and registration
- object tracking persistence
- the older demo flows for audio evidence binding and object lookup

It is not yet fully integrated with:

- a canonical current application entrypoint,
- a formal service boundary,
- or the future Reasoning layer.

---

## 2. Repository Reality Check

### Intended architecture vs actual implementation
The intended architecture suggests a modular system where each subsystem has a clear boundary. In the repository, the implementation is partially aligned with that goal, but it is still mixed with archived demo code and older module paths.

### What is finished
The following parts are already implemented and visible in the repository:

- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)
- [src/vision/face_recognizer.py](src/vision/face_recognizer.py)
- [src/audio/audio_listener.py](src/audio/audio_listener.py)
- [src/reasoning/context_binder.py](src/reasoning/context_binder.py)
- [src/mapping/spatial_slam.py](src/mapping/spatial_slam.py)

### What is partially finished
The following are only partially finished:

- the app flow in [app.py](app.py), which is empty,
- the settings layer in [config/settings.py](config/settings.py), which is empty,
- the constants layer in [config/constants.py](config/constants.py), which is empty,
- the paths layer in [config/paths.py](config/paths.py), which is empty,
- the current integration between audio evidence and the Memory layer,
- and the active object-tracking integration path.

### What is obsolete
The older demo implementations are still present in the archive:

- [archive/week1/demo_week1.py](archive/week1/demo_week1.py)
- [archive/week2/demo_week2.py](archive/week2/demo_week2.py)

These are useful as historical references, but they should not be treated as the primary implementation path for the current Memory subsystem.

### What exists only inside archive
The following flows are present primarily in archive demos rather than the current source tree:

- the full voice-driven identity-binding loop,
- the object-detection-to-database flow,
- and the older app orchestration model.

### What is actively used
The currently active source modules used by the Memory subsystem are:

- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)
- [src/vision/face_recognizer.py](src/vision/face_recognizer.py)

### What is no longer used
The older imports from the legacy `core` layout are not part of the active current source tree; the current code is pointing toward the [src](src) package structure, while some archive demos still reference the older `core` package paths.

### What is duplicated
There is some duplication of responsibility across:

- the older demo orchestration logic,
- the current source modules,
- and the Memory database methods themselves.

The biggest duplication is the fact that identity-binding and object-logging logic is partially repeated across the archive demos and the current core modules.

---

## 3. Team Task Verification

### Original team plan
The plan said the Memory Lead would own:

- `database.py`
- `person_memory.py`
- `event_memory.py`
- `object_memory.py`

### Actual repository verification

#### Planned files that already exist
The repository contains:

- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)

#### Planned files that do not exist
The current repository does not contain files named:

- `person_memory.py`
- `event_memory.py`
- `object_memory.py`

#### Planned responsibilities that are already completed
The following responsibilities already exist inside current files:

- identity persistence in [src/memory/database.py](src/memory/database.py)
- object persistence in [src/memory/database.py](src/memory/database.py)
- basic object-tracking logic in [src/memory/object_ledger.py](src/memory/object_ledger.py)

#### Planned responsibilities that changed
The original plan appears to have been split across different implementations:

- identity memory is implemented inside [src/memory/database.py](src/memory/database.py)
- object memory is partly implemented inside [src/memory/database.py](src/memory/database.py) and partly inside [src/memory/object_ledger.py](src/memory/object_ledger.py)

#### Responsibilities still pending
The following responsibilities are still pending or incomplete:

- a clean, dedicated person-memory abstraction,
- a dedicated event-memory abstraction,
- a clearer object-memory abstraction,
- and stronger integration of these concepts under a single consistent Memory API.

---

## 4. Existing Memory APIs

The following are the public Memory APIs that currently exist in the repository.

| API | Purpose | Who calls it | Who depends on it | Can it be modified? | Can it be extended? | Should it remain untouched? | Risk |
|---|---|---|---|---|---|---|---|
| `MemoraDatabase.register_anonymous(...)` | Create a new anonymous identity and store the first embedding | [src/vision/face_recognizer.py](src/vision/face_recognizer.py) | Vision and future identity flows | Yes, but carefully | Yes | No, not blindly | High |
| `MemoraDatabase.add_embedding_to_identity(...)` | Add a new embedding to an existing identity | currently limited use | future reinforcement flows | Yes | Yes | No, not blindly | Medium |
| `MemoraDatabase.update_embedding_ema(...)` | Update an existing embedding using EMA | [src/vision/face_recognizer.py](src/vision/face_recognizer.py) | Vision | Yes, but carefully | Yes | No, not blindly | Medium |
| `MemoraDatabase.increment_times_seen(...)` | Update visit count and timestamp | [src/vision/face_recognizer.py](src/vision/face_recognizer.py) | Vision | Yes | Yes | No, not blindly | Low |
| `MemoraDatabase.bind_name(...)` | Bind a name and relationship to an identity | currently limited use | future confirm/identity flows | Yes | Yes | No, not blindly | Medium |
| `MemoraDatabase.get_identity(...)` | Retrieve an identity profile | [src/vision/face_recognizer.py](src/vision/face_recognizer.py) | Vision and future UI/debug flows | Yes | Yes | No, not blindly | Medium |
| `MemoraDatabase.get_all_identities(...)` | Return all identities | likely future inspection/debug/analytics | future maintenance tools | Yes | Yes | No, not blindly | Low |
| `MemoraDatabase.log_object(...)` | Record object sightings and locations | [archive/week2/demo_week2.py](archive/week2/demo_week2.py) | object-tracking flow | Yes | Yes | No, not blindly | Medium |
| `MemoraDatabase.get_last_known_location(...)` | Retrieve the latest object location | [archive/week2/demo_week2.py](archive/week2/demo_week2.py) | object-query flow | Yes | Yes | No, not blindly | Medium |
| `MemoraDatabase.get_object_history(...)` | Return historical sightings for an object | future tools | future object-query/debug flows | Yes | Yes | No, not blindly | Low |
| `MemoraDatabase.set_current_room(...)` | Set the current room | [archive/week2/demo_week2.py](archive/week2/demo_week2.py) | mapping/object context | Yes | Yes | No, not blindly | Low |
| `MemoraDatabase.get_current_room(...)` | Retrieve the current room | [archive/week2/demo_week2.py](archive/week2/demo_week2.py) | mapping/object context | Yes | Yes | No, not blindly | Low |
| `MemoraDatabase.clear(...)` | Clear all database contents | tests and local experimentation | future testing/dev workflows | Yes | Yes | No, not blindly | Medium |
| `MemoraDatabase.add_evidence(...)` | Add voice-based evidence and update confidence | older demo flow | audio/context-binding integration | Yes | Yes | No, not blindly | High |
| `MemoraDatabase.get_candidates(...)` | Retrieve candidate evidence entries | older demo flow | audio/context-binding integration | Yes | Yes | No, not blindly | Low |
| `MemoraObjectTracker.detect_objects(...)` | Run object detection and produce detections | legacy/object demo flow | object tracking | Yes, but not a core Memory API | Yes | Not relevant to the Memory Lead’s core task | Medium |
| `MemoraObjectTracker.draw_ledger_overlay(...)` | Draw visual overlay for object tracker | visualization | UI | No need to alter for core memory work | No | Leave untouched unless required | Low |

### Guidance for the Memory Lead
The safest rule is:

- preserve the shape of existing methods,
- extend them rather than replace them,
- and avoid changing semantics without a compatibility plan.

---

## 5. Dependency Analysis

### Dependency map: Vision → Memory

```text
[src/vision/face_recognizer.py](src/vision/face_recognizer.py)
  ↓
MemoraFaceRecognizer.process_frame(...)
  ↓
MemoraDatabase.find_match(...)
  ↓
SQLite face_embeddings + identities
  ↓
MemoraDatabase.get_identity(...)
  ↓
Identity profile returned
```

### Dependency map: identity registration

```text
[src/vision/face_recognizer.py](src/vision/face_recognizer.py)
  ↓
MemoraFaceRecognizer.process_frame(...)
  ↓
MemoraDatabase.register_anonymous(...)
  ↓
SQLite identities
  ↓
SQLite face_embeddings
  ↓
SQLite system_state
```

### Dependency map: embedding reinforcement

```text
[src/vision/face_recognizer.py](src/vision/face_recognizer.py)
  ↓
MemoraDatabase.update_embedding_ema(...)
  ↓
SQLite face_embeddings
```

### Dependency map: visit counting

```text
[src/vision/face_recognizer.py](src/vision/face_recognizer.py)
  ↓
MemoraDatabase.increment_times_seen(...)
  ↓
SQLite identities
```

### Dependency map: object logging

```text
[archive/week2/demo_week2.py](archive/week2/demo_week2.py)
  ↓
MemoraDatabase.log_object(...)
  ↓
SQLite objects
  ↓
SQLite object_history
```

### Dependency map: room state

```text
[archive/week2/demo_week2.py](archive/week2/demo_week2.py)
  ↓
MemoraDatabase.set_current_room(...)
  ↓
SQLite system_state
```

### Dependency map: evidence accumulation

```text
[archive/week1/demo_week1.py](archive/week1/demo_week1.py)
  ↓
MemoraDatabase.add_evidence(...)
  ↓
SQLite identity_evidence
  ↓
SQLite identities
```

---

## 6. What Can Be Changed Safely

### 🟢 Safe to modify
These are the safest areas for the Memory Lead to modify because they are either internal implementation details or read-oriented enhancements:

- `MemoraDatabase.get_all_identities(...)`
- `MemoraDatabase.get_object_history(...)`
- `MemoraDatabase.get_candidates(...)`
- `MemoraDatabase.get_current_room(...)`
- `MemoraDatabase.get_last_known_location(...)`
- `MemoraDatabase.get_identity(...)`

Why these are safe:

- they are mostly read-paths,
- they have limited direct coupling to the live vision loop,
- and they can often be extended without breaking the semantics of the caller.

### 🟡 Safe to extend
These can be extended if the Memory Lead preserves their current behavior and output shape:

- `MemoraDatabase.register_anonymous(...)`
- `MemoraDatabase.add_embedding_to_identity(...)`
- `MemoraDatabase.update_embedding_ema(...)`
- `MemoraDatabase.increment_times_seen(...)`
- `MemoraDatabase.bind_name(...)`
- `MemoraDatabase.log_object(...)`
- `MemoraDatabase.add_evidence(...)`

Why these are safe to extend:

- they already support the current ecosystem,
- and new fields or internal behavior can be added while preserving the current return values and table semantics.

### 🔴 Do NOT modify lightly
These should be treated as compatibility-sensitive and should not be changed casually:

- `MemoraDatabase.find_match(...)`
- `MemoraDatabase.register_anonymous(...)` if its return format or identity semantics change
- `MemoraDatabase.add_evidence(...)` if the confidence logic or status semantics change without careful review
- `MemoraDatabase.log_object(...)` if the object-history behavior changes unexpectedly

Why these should not be modified lightly:

- they are directly involved in the existing runtime behavior of Vision and the archive demos,
- and changing them can silently break identity matching, identity creation, or evidence accumulation.

### Strong recommendation
The Memory Lead should prefer adding behavior over replacing behavior. The current subsystem is a working prototype, so the lowest-risk path is extension, not redesign.

---

## 7. Missing Features

The following memory-related features are still missing or incomplete.

### High priority
1. A canonical settings contract
   - [config/settings.py](config/settings.py) is empty.
   - The Memory module depends on settings values that are currently missing.

2. A current app entrypoint that uses the actual source modules
   - [app.py](app.py) is empty.
   - The current runtime flow is still rooted in archive demos rather than the active package tree.

3. A stable integration path for audio evidence into the current source modules
   - the evidence-binding path exists in the archive demo, but the active source layout is not fully wired to it.

4. A more formal object-memory integration path
   - object logging works, but it is not fully unified with the rest of the memory subsystem.

5. Tests for Memory behavior
   - the repository currently contains no active test files under [tests](tests) beyond the workspace skeleton.

### Medium priority
6. A richer identity profile model
   - current identity records are still fairly minimal.

7. More robust embedding lifecycle handling
   - multiple embeddings and EMA are present, but no stronger retention or quality policy exists.

8. Better error handling around database corruption or missing schema elements
   - the current initialization path already attempts migration logic, but it is still fairly basic.

### Low priority
9. Better observability around Memory operations
   - there is a central logger, but the Memory layer does not expose an explicit audit trail beyond its current print-based event flow.

---

## 8. Configuration Problems

### Inspection results
The following configuration files exist but are incomplete:

- [config/settings.py](config/settings.py)
- [config/constants.py](config/constants.py)
- [config/paths.py](config/paths.py)
- [.env.example](.env.example)

### Missing settings
The current code expects configuration values such as:

- `DB_PATH`
- `FACE_TOLERANCE`
- `SPATIAL_CELL_SIZE`
- `TRACKED_OBJECTS`
- `YOLO_MODEL_NAME`
- `DEBUG`
- `GEMINI_API_KEY`

These values are referenced in the repository, but the current settings file is empty.

### Which modules depend on them
- [src/memory/database.py](src/memory/database.py) depends on `DB_PATH` and `FACE_TOLERANCE`.
- [src/memory/object_ledger.py](src/memory/object_ledger.py) depends on `SPATIAL_CELL_SIZE`, `TRACKED_OBJECTS`, and `YOLO_MODEL_NAME`.
- [src/vision/face_recognizer.py](src/vision/face_recognizer.py) depends on `FACE_TOLERANCE` and `DEBUG`.
- [src/audio/audio_listener.py](src/audio/audio_listener.py) depends on `DEBUG`.
- [src/reasoning/context_binder.py](src/reasoning/context_binder.py) depends on `GEMINI_API_KEY`.

### Risk level
High. The current configuration gap is a real integration risk. If the Memory Lead changes the database layer without a stable settings contract, other modules may fail or behave unexpectedly.

### Does Memory depend on them?
Yes. The Memory subsystem depends directly on the settings file for basic database and tolerance behavior.

---

## 9. Current Bugs

The following issues should be treated as important before adding features.

### 1. Settings are missing at runtime
- Evidence: importing `config.settings` in the current environment returned missing attributes.
- Risk: high
- Impact: Memory and Vision cannot reliably use the expected defaults.

### 2. `find_match(...)` is a brute-force scan
- The method loops through every stored embedding.
- Risk: medium-to-high as the identity count grows.
- Impact: performance degradation.

### 3. No transaction rollback path is visible
- The database layer uses commit operations but no explicit rollback handling.
- Risk: medium
- Impact: inconsistent state if a write partially fails.

### 4. `load()` and `save()` are placeholders
- In [src/memory/database.py](src/memory/database.py), `load()` and `save()` are defined but do nothing.
- Risk: medium
- Impact: the database class is less consistent and may be confusing for future maintainers.

### 5. `clear()` deletes data without a safer lifecycle wrapper
- Risk: medium
- Impact: easy to wipe state accidentally during local debugging.

### 6. Object history retention is hard-coded at 50 rows
- Risk: low-to-medium
- Impact: this is acceptable for a prototype, but it is an implementation choice that should be documented explicitly.

### 7. The Memory module is tightly coupled to direct Vision calls
- Risk: medium
- Impact: any change to the Memory API can affect the recognition pipeline.

### 8. The current repo has a split architecture between old and new module paths
- Risk: medium
- Impact: the Memory Lead may waste time working in paths that are no longer canonical.

### 9. The context-binder path has a likely client mismatch
- The active file [src/reasoning/context_binder.py](src/reasoning/context_binder.py) uses `self.client.models.generate_content(...)` and also references `self.model` in one method.
- This is not directly in the Memory subsystem, but it affects the audio evidence flow that Memory depends on.
- Risk: medium

---

## 10. Integration Gaps

### Memory ↔ Vision
- Status: implemented, but partially coupled.
- Evidence: [src/vision/face_recognizer.py](src/vision/face_recognizer.py) calls `MemoraDatabase.find_match(...)`, `register_anonymous(...)`, `update_embedding_ema(...)`, `increment_times_seen(...)`, and `get_identity(...)` directly.
- Risk: medium-high because the current integration is implementation-driven rather than API-driven.

### Memory ↔ Audio
- Status: partial.
- Evidence: the older flow in [archive/week1/demo_week1.py](archive/week1/demo_week1.py) uses `db.add_evidence(...)`, but the active source modules do not yet present a clean, canonical way to connect audio evidence to the Memory subsystem.
- Risk: medium.

### Memory ↔ Object Tracker
- Status: partial.
- Evidence: object tracking logic exists in [src/memory/object_ledger.py](src/memory/object_ledger.py), but the active database persistence path is mostly seen in the archive demo [archive/week2/demo_week2.py](archive/week2/demo_week2.py).
- Risk: medium.

### Memory ↔ Reasoning
- Status: missing/partial.
- Evidence: [src/reasoning/context_binder.py](src/reasoning/context_binder.py) exists, but the current Memory layer does not expose a clean reasoning-facing service contract.
- Risk: medium.

### Memory ↔ Mapping
- Status: partial.
- Evidence: [src/mapping/spatial_slam.py](src/mapping/spatial_slam.py) and [src/memory/database.py](src/memory/database.py) both deal with room context, but they are not yet combined into a stable, shared representation.
- Risk: low-to-medium.

---

## 11. Testing Status

### Existing tests
The repository currently contains a [tests](tests) directory, but it is effectively empty in the current workspace state. The earlier test files referenced in the repository summary are not present in the active tree.

### Coverage
No meaningful Memory-specific test coverage is currently available in the active repository snapshot.

### Missing tests
The Memory Lead should add tests for:

- anonymous identity registration,
- identity lookup,
- face embedding matching,
- evidence accumulation,
- object history persistence,
- room-state persistence,
- and database clear/reset behavior.

### Critical tests
These should be considered mandatory before merge:

- `register_anonymous(...)` creates both identity and embedding records.
- `find_match(...)` returns the correct identity for a matching embedding.
- `add_evidence(...)` updates confidence and status as expected.
- `log_object(...)` writes both the current object record and history rows.
- `get_last_known_location(...)` returns the latest data.
- `clear()` resets the database to a consistent empty state.

### Recommended test style
The Memory Lead should prioritize:

- unit tests for each public method,
- integration tests around the SQLite file,
- and a regression test for any change to schema semantics.

---

## 12. Git Impact Analysis

### If the Memory Lead changes `database.py`
Likely impact:

- Vision matching behavior may change if `find_match(...)` semantics change.
- Identity registration may break if `register_anonymous(...)` changes its return value or database writes.
- Audio evidence integration may break if `add_evidence(...)` changes status or confidence behavior.
- Object logging may break if `log_object(...)` changes the schema or history semantics.

### If the Memory Lead changes `find_match()`
Likely impact:

- the Vision recognition pipeline may stop matching identities correctly,
- identity promotion decisions may change,
- and any application relying on the current nearest-neighbor behavior will be affected.

### If the Memory Lead changes `register_anonymous()`
Likely impact:

- the identity lifecycle may be altered,
- newly promoted face tracks may be assigned different IDs,
- and downstream code that expects the current ID format may break.

### If the Memory Lead changes `add_evidence()`
Likely impact:

- audio-driven confirmation may change,
- the `identity_evidence` table semantics may shift,
- and the confidence and `confirmed` status logic may break.

### If the Memory Lead changes `log_object()`
Likely impact:

- object-tracking history will change,
- last-known-location behavior may shift,
- and the object query flow may regress.

### Core rule
The Memory Lead should avoid changing the public contract of the Memory API unless the change is coordinated and tested against the existing runtime behavior.

---

## 13. Recommended Development Roadmap

### Milestone 1 — Stabilize current Memory contract
Objective:
- preserve current behavior while making it easier to reason about.

Files:
- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)

Functions:
- `MemoraDatabase.register_anonymous(...)`
- `MemoraDatabase.find_match(...)`
- `MemoraDatabase.get_identity(...)`

Dependencies:
- current SQLite schema
- current Vision call sites

Difficulty:
- medium

Definition of Done:
- the current Vision workflow still works,
- the existing methods remain compatible,
- and the behavior is documented.

### Milestone 2 — Fill the configuration gap
Objective:
- define the settings the Memory subsystem actually needs.

Files:
- [config/settings.py](config/settings.py)
- [config/constants.py](config/constants.py)
- [config/paths.py](config/paths.py)

Functions:
- no direct Memory methods, but required to stabilize runtime behavior

Dependencies:
- Memory and Vision imports

Difficulty:
- low-to-medium

Definition of Done:
- the Memory subsystem can load default runtime values from the settings layer.

### Milestone 3 — Add Memory tests
Objective:
- lock in the current contract with tests before future changes.

Files:
- [tests](tests)

Functions:
- all public Memory methods that are currently used by Vision and object tracking

Dependencies:
- temporary SQLite database handling

Difficulty:
- medium

Definition of Done:
- tests cover the happy path and the edge cases of registration, match, evidence, and object logging.

### Milestone 4 — Improve the database abstraction
Objective:
- make the database layer more explicit and less ad hoc without breaking the current API.

Files:
- [src/memory/database.py](src/memory/database.py)

Functions:
- `load(...)`, `save(...)`, and the initialization path

Dependencies:
- current SQLite schema

Difficulty:
- medium

Definition of Done:
- the database layer has clearer lifecycle handling and better internal consistency.

### Milestone 5 — Integrate audio evidence more cleanly
Objective:
- connect the audio/context-binding flow to the current source modules rather than only the archive demo.

Files:
- [src/reasoning/context_binder.py](src/reasoning/context_binder.py)
- [src/audio/audio_listener.py](src/audio/audio_listener.py)
- [src/memory/database.py](src/memory/database.py)

Dependencies:
- Memory evidence logic

Difficulty:
- medium

Definition of Done:
- the Memory subsystem can receive evidence from the current source flow without relying on the archive demo.

### Milestone 6 — Formalize object-memory integration
Objective:
- make object logging and object-history retrieval a first-class part of the Memory subsystem.

Files:
- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)

Dependencies:
- object tracker and database flow

Difficulty:
- medium

Definition of Done:
- object memory is clearly documented and relied on by the current runtime path rather than only the archive demo.

### Milestone 7 — Plan for future scalability
Objective:
- prepare the Memory subsystem for higher scale without rewriting it immediately.

Files:
- [src/memory/database.py](src/memory/database.py)

Dependencies:
- matching and embedding lifecycle

Difficulty:
- high

Definition of Done:
- the Memory Lead has documented a path for future indexing or retrieval improvements without breaking the current API.

---

## 14. Daily Task Plan

### Day 1
Objective:
- understand the current Memory contract and identify the active call sites.

Files:
- [src/memory/database.py](src/memory/database.py)
- [src/vision/face_recognizer.py](src/vision/face_recognizer.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)

Expected commits:
- `docs(memory): document current API contract`

Testing:
- no code changes yet; validate understanding through repo inspection.

Integration checkpoints:
- confirm which methods are used by Vision and object tracking.

### Day 2
Objective:
- stabilize runtime configuration and document the required settings.

Files:
- [config/settings.py](config/settings.py)
- [config/constants.py](config/constants.py)
- [config/paths.py](config/paths.py)

Expected commits:
- `docs(memory): record required settings`

Testing:
- import and instantiate the Memory classes with the current workspace state.

Integration checkpoints:
- verify that the Memory layer can start without missing configuration values.

### Day 3
Objective:
- add foundational tests for the current Memory API.

Files:
- [tests](tests)

Expected commits:
- `test(memory): add core database lifecycle tests`

Testing:
- run the new tests locally.

Integration checkpoints:
- validate anonymous registration and lookup behavior.

### Day 4
Objective:
- improve the database lifecycle and internal robustness.

Files:
- [src/memory/database.py](src/memory/database.py)

Expected commits:
- `fix(memory): make database lifecycle behavior explicit`

Testing:
- rerun the core tests and verify no regressions.

Integration checkpoints:
- confirm that Vision still receives the expected output shape.

### Day 5
Objective:
- connect the audio evidence path more cleanly to current source modules.

Files:
- [src/audio/audio_listener.py](src/audio/audio_listener.py)
- [src/reasoning/context_binder.py](src/reasoning/context_binder.py)
- [src/memory/database.py](src/memory/database.py)

Expected commits:
- `refactor(memory): align evidence path with current source modules`

Testing:
- test the evidence path with a synthetic transcript.

Integration checkpoints:
- ensure that identity confidence updates still work.

### Day 6
Objective:
- formalize object-memory persistence and retrieval.

Files:
- [src/memory/database.py](src/memory/database.py)
- [src/memory/object_ledger.py](src/memory/object_ledger.py)

Expected commits:
- `feat(memory): clarify object history and lookup paths`

Testing:
- verify object persistence and retrieval behavior.

### Day 7
Objective:
- write the handoff summary and produce a clean PR plan.

Files:
- [docs](docs)

Expected commits:
- `docs(memory): prepare handoff and PR notes`

---

## 15. Commit Strategy

A sensible commit order would be:

1. `docs(memory): document current Memory contract`
2. `docs(memory): record required settings and runtime assumptions`
3. `test(memory): add core database lifecycle tests`
4. `fix(memory): stabilize schema initialization and lifecycle behavior`
5. `refactor(memory): clarify evidence and identity flow`
6. `feat(memory): strengthen object-memory integration`
7. `docs(memory): prepare PR notes and handoff summary`

This order keeps the work safe because it moves from understanding, to validation, to stabilization, and then to feature work.

---

## 16. Pull Request Readiness Checklist

Before opening a PR, the Memory Lead should verify:

### Database
- [ ] the SQLite schema still initializes correctly,
- [ ] the database file is created in the expected location,
- [ ] existing rows are not corrupted,
- [ ] the migration path is still safe.

### Tests
- [ ] core unit tests pass,
- [ ] integration tests around the database pass,
- [ ] no regressions appear in the identity and object flows.

### API compatibility
- [ ] existing method signatures are preserved unless deliberately changed,
- [ ] return values remain compatible with the current callers,
- [ ] any new behavior is additive rather than breaking.

### Vision compatibility
- [ ] Vision still receives the same sort of result structure,
- [ ] `find_match(...)` still behaves as expected for known identities,
- [ ] anonymous registration still occurs in the expected path.

### Thread safety
- [ ] the locking strategy still protects the database operations,
- [ ] no new concurrent access issues were introduced.

### Configuration
- [ ] required settings are documented,
- [ ] default values are safe,
- [ ] config gaps are either fixed or intentionally deferred.

### Documentation
- [ ] the Memory contract is documented,
- [ ] the public API is described,
- [ ] the risks and limitations are clear.

### Git status
- [ ] the commit set is focused and reviewed,
- [ ] no stray files are included,
- [ ] the diff is easy to review.

### Code quality
- [ ] naming is consistent,
- [ ] comments are accurate,
- [ ] no dead code was introduced,
- [ ] no unrelated refactors were bundled into the PR.

---

## 17. Architectural Risks

If the Memory Lead ignores the architecture and changes the subsystem too aggressively, the following risks appear:

### Breaking Vision
Changing the matching semantics or the output of `find_match(...)` could break the Vision recognition pipeline.

### Breaking object tracking
Changing the object-memory data shape or history semantics could break the object query flow and the object tracker assumptions.

### Breaking embeddings
Changing how embeddings are stored, compared, or EMA-updated could change identity recognition behavior without any obvious error.

### Breaking identity lifecycle
Changing the naming or status semantics of `identities` could break the evidence-confirmation flow and make newly registered identities behave incorrectly.

### Introducing silent data corruption
Changing the database write path without preserving the current semantics could leave the SQLite database in an inconsistent state.

### Creating a split-brain architecture
If the Memory Lead introduces a new abstraction without preserving the existing flow, Vision may continue using the old path while new paths evolve separately.

---

## 18. Technical Mentor Advice

### Best practices
- preserve the current API shape while extending behavior,
- prefer additive changes over semantic rewrites,
- document every change to the database schema or method contract,
- and keep the current Vision call sites in mind while editing.

### Common mistakes
- changing `find_match(...)` without validating the recognition pipeline,
- changing `register_anonymous(...)` semantics without updating downstream expectations,
- introducing a new storage layer without preserving the existing SQLite-backed behavior,
- and over-engineering the Memory layer before the current contract is stable.

### Things to avoid
- rewriting the subsystem from scratch,
- introducing new abstractions that are not yet needed,
- changing the database schema without a migration plan,
- touching archive code as a primary implementation path,
- and adding features before tests exist.

### Things to prioritize
- configuration stabilization,
- test coverage,
- compatibility preservation,
- and clear documentation.

### Coding advice
- keep changes small and explainable,
- write tests before broad refactors,
- and prefer disciplined extension over redesign.

### Architecture advice
- treat the current Memory subsystem as a working prototype that must remain stable for the rest of the platform.

### Git advice
- keep PRs focused,
- avoid mixing schema changes with unrelated refactors,
- and make sure every change is easy to review.

### Testing advice
- test the public methods that the rest of the system depends on,
- and include at least one integration test that uses the SQLite file directly.

---

## 19. Final Verdict

### What EXACTLY should the Memory Lead build?
The Memory Lead should build a more stable, documented, tested, and configuration-safe version of the existing Memory subsystem. The core task is not to redesign Memory, but to harden what already exists.

### What should NOT be touched?
The Memory Lead should not rewrite the architecture, remove the current database-backed methods, or change the semantics of the core identity and object lifecycle without a compatibility plan.

### What should be refactored later?
A cleaner service boundary, richer abstractions for person/event/object memory, and a future indexing strategy can be deferred until the current contract is stable.

### What should be documented?
The Memory Lead should document:

- the public API,
- the current database schema behavior,
- the expected settings contract,
- and the current integration points with Vision and object tracking.

### What should be tested?
The Memory Lead should test:

- registration,
- matching,
- evidence accumulation,
- object logging,
- room-state persistence,
- and database reset behavior.

### What should be committed first?
The first commit should be a documentation and test-focused stabilization step, not a major feature rewrite.

### What should be merged last?
The biggest architectural enhancements should be merged last, after the Memory contract is stable and tested.

### What is the safest order of implementation?
1. document and stabilize,
2. add tests,
3. fix configuration and lifecycle issues,
4. improve integration points,
5. then consider larger enhancements.

### If you were the Technical Lead, what work would you assign the Memory Lead starting tomorrow?
I would assign the Memory Lead the following work starting tomorrow:

1. read and document the current Memory API and call sites,
2. define the runtime settings required by the Memory subsystem,
3. write tests for the core methods,
4. preserve compatibility while making the database layer easier to reason about,
5. and connect the audio evidence path to the current source modules without breaking the Vision flow.
