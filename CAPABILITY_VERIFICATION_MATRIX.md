# MEMORA — Capability Verification Matrix

_Updated 2026-10-20 (cycle 2). Labels:_
**IMPLEMENTED** code exists and is wired into a supported entry point ·
**TESTED** automated tests exercise the real path with meaningful assertions ·
**SIMULATED** verified only with simulated sensors/data ·
**HARDWARE-UNVERIFIED** needs a real camera/microphone/speaker/device ·
**EXTERNALLY-UNVERIFIED** depends on a third-party service not exercised ·
**BLOCKED** cannot proceed without an owner decision or outside party.
_No capability has real-world, clinical, or usability evidence._

How to invoke: `python app.py --chat` (C), `--simulate` (S), `--check` (K), runtime `python app.py [--simulation|--live-hardware]` (R).

| Capability | Status | Path | Invoke | Evidence | Limitations / remaining risk | Next action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Consent before storage | IMPLEMENTED, TESTED | `consent_manager.py`, chat onboarding, `memory_storage_allowed` | C: first run, `/consent` | `test_consent_enforcement.py`, `test_chat_and_user_data.py`, journeys `first_time_onboarding`, `consent_declined` | Consent is per database, not per person | Caregiver-mediated consent flow (needs product/legal input) |
| Face-recognition consent | IMPLEMENTED, TESTED, HARDWARE-UNVERIFIED | recogniser `consent_check` set by coordinator | `/consent faces on` | `test_consent_enforcement.py` (synthetic frames) | Real recognition untested | Test with consenting people on a real camera |
| Text conversation | IMPLEMENTED, TESTED | `src/application/chat.py` | C | 20 journeys; Docker CI job; piped sessions | Rule-based; bounded phrasing | Grow corpus from consented usage |
| Facts with provenance; corrections; retraction | IMPLEMENTED, TESTED | `conversational_memory.py` | C | `test_conversational_memory.py`, corpus (51 cases), journeys | One person per database | — |
| Conflicting relations surfaced | IMPLEMENTED, TESTED | same | C | `test_second_daughter_is_kept_and_conflict_surfaced`, journey `conflicting_memories` | — | — |
| Honest unknown/ambiguous answers | IMPLEMENTED, TESTED | same | C | journey `unknown_and_ambiguous` | — | — |
| Orientation (time/date) | IMPLEMENTED, TESTED | same + care policy | C | journey `names_and_time` (simulated clock) | Location is never asserted | — |
| Urgent-situation guidance | IMPLEMENTED, TESTED | `urgent_safety.py`, care policy | C/R | `test_urgent_safety.py` (31 cases), journey `urgent_distress` | English keywords; not clinically validated | Clinical review of phrase set |
| Output safety guard | IMPLEMENTED, TESTED | `response_guard.py` on the delivery path | all | `test_response_guard_and_boundaries.py` | Pattern-based; may over-block | — |
| Capability / medical boundaries | IMPLEMENTED, TESTED | `_capability_boundaries` | C | same + journey `medical_boundaries` | — | — |
| Emergency number / trusted contact | IMPLEMENTED, TESTED | chat `/set-…`, system_state | C | `test_urgent_safety.py`, journey `urgent_distress` | Numbers not validated against local emergency systems | — |
| Medication schedules, reminders, reported doses | IMPLEMENTED, TESTED | `MedicationManager`, `CareStore` | C | `test_care_schedules.py`, journey `reminders_and_throttling` | Never verifies intake; no quiet-hours policy (deliberate, see `docs/SAFETY_AND_LIMITATIONS.md`) | Caregiver review of reminder wording |
| Appointments | IMPLEMENTED, TESTED | `AppointmentManager`, `CareStore` | C | `test_care_schedules.py` | — | — |
| Known / unknown visitor handling | IMPLEMENTED, SIMULATED | pipeline `_is_known_visitor_arrival` | R | journeys `known_visitor`, `unknown_visitor`, `self_is_not_a_visitor`; scenario CS-11 | Synthetic recognition results only | Real camera test |
| Object "last seen" with source and age | IMPLEMENTED, TESTED, SIMULATED | `conversational_memory`, `objects.source` | C/R | journeys `simulated_object_observation`, `stale_object_observation`; `test_observation_provenance_is_stated` | Real detection is a contour heuristic (experimental) | Licence-compatible detector |
| Schema migrations | IMPLEMENTED, TESTED | `src/memory/migrations.py` | automatic | `test_migrations.py` incl. copy of the local DB | Additive only | — |
| Persistence across restart | IMPLEMENTED, TESTED | SQLite + per-DB embeddings | C | journey `restart_persistence`; Docker CI job | — | — |
| View / export / delete (incl. logs) | IMPLEMENTED, TESTED | `user_data.py`, chat | C | `test_chat_and_user_data.py`, `test_failure_handling_and_deletion.py`, journey `export_and_delete` | Backups are not deleted (the person is told); no secure erase | — |
| Backup / restore (incl. corrupt live DB) | IMPLEMENTED, TESTED | `src/memory/backup.py` | `--backup`, `--restore` | `test_backup_restore.py`, journey `backup_and_corruption_recovery` | Stop MEMORA before restoring | — |
| Storage-failure handling | IMPLEMENTED, TESTED | `open_user_database` | C/R | `test_failure_handling_and_deletion.py` (real CLI subprocess) | — | — |
| Repair of faceless identities | IMPLEMENTED, TESTED | `--repair` | `--repair` | tests on copies | — | Owner decision for the local DB |
| Simulation (clock, battery, sensor failure, journeys) | IMPLEMENTED, TESTED, SIMULATED | `src/simulation/` | S | `test_simulation_journeys.py` (20 journeys + runner meta-tests) | Simulated only | — |
| Runtime status / diagnostics | IMPLEMENTED, TESTED | `AnchorRuntime.get_subsystem_statuses`, `--check` | K/R | `test_honest_runtime_reporting.py`, journey `sensor_unavailable` | — | — |
| No physical devices in tests | IMPLEMENTED, TESTED | `tests/conftest.py` guard | — | `test_no_physical_devices.py` | — | — |
| Stability | SIMULATED | soak harness | `deployment/benchmarks/soak_runtime.py` | `docs/evidence/` (10–20 min soaks) | ≤ 20 min, simulated | Multi-hour soak; real hardware |
| Camera, microphone, ASR, TTS | HARDWARE-UNVERIFIED | `src/runtime/*_adapter.py` | R `--live-hardware` | none on real devices (tests block real devices) | Never run on hardware in this work | Owner authorisation for device testing |
| Face recognition (real faces) | HARDWARE-UNVERIFIED, BLOCKED (licensing) | `face_recognizer.py` | R | synthetic only | InsightFace models are non-commercial | Licence decision |
| Object detection (real) | HARDWARE-UNVERIFIED, BLOCKED (licensing for YOLO) | `object_detector.py`, `object_ledger.py` | R | none | Contour heuristic; YOLO is AGPL-3.0 | Replace or license |
| Gemini name extraction | EXTERNALLY-UNVERIFIED | `context_binder.py` | R (identity learning) | fake-client tests | No key; API terms need review | Owner-provided test key |
| Dashboard (developer view) | IMPLEMENTED, TESTED (browser, synthetic events) | `experience/` | `--dashboard` | browser check with hostile input | Telemetry view, not a carer product | — |
| Docker deployment | IMPLEMENTED, TESTED | `deployment/docker/Dockerfile` | docker | local runs + CI Docker job | Core text mode only | — |
| Clean install / CI | IMPLEMENTED, TESTED | `requirements*.txt`, `.github/workflows/ci.yml` | — | fresh clone 664 passed + 2 skipped (`8ccf2bd`); CI on Linux x86-64 | Core verified on Python 3.11 (macOS, CI), 3.12 and 3.13 (clean containers, `ac87a0f`: 747 passed, 6 skipped with reasons). Microphone capture (optional SpeechRecognition) does not support 3.13 | — |
| Platforms | — | — | — | macOS arm64 (native), Linux arm64 (Docker), Linux x86-64 (CI) | Windows, Raspberry Pi, wearables untested | — |
