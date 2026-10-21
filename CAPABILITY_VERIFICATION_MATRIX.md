# MEMORA — Capability Verification Matrix

_Updated 2026-10-21 (final completion mission). Labels:_
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
| Consent before storage (every write path: conversation, commands, reported doses, identity learning, logs) | IMPLEMENTED, TESTED | `consent_manager.py` (`ConsentRequiredError`), chat onboarding, `memory_storage_allowed`, `CareStore` | C: first run, `/consent` | `test_consent_policy.py` (persisted state; marker absent from every file), `test_consent_enforcement.py`, `test_chat_and_user_data.py`, journeys `first_time_onboarding`, `consent_declined`; policy `docs/PRIVACY_AND_CONSENT.md` | Consent is per database, not per person | Caregiver-mediated consent flow (needs product/legal input) |
| Face-recognition consent | IMPLEMENTED, TESTED, HARDWARE-UNVERIFIED | recogniser `consent_check` set by coordinator | `/consent faces on` | `test_consent_enforcement.py` (synthetic frames) | Real recognition untested | Test with consenting people on a real camera |
| Text conversation | IMPLEMENTED, TESTED | `src/application/chat.py` | C | 20 journeys; Docker CI job; piped sessions | Rule-based; bounded phrasing | Grow corpus from consented usage |
| Facts with provenance; corrections (incl. "Actually…", "No, …"); retraction | IMPLEMENTED, TESTED | `conversational_memory.py` | C | `test_conversational_memory.py`, corpus (51 cases), journeys, `test_cli_end_to_end.py` | One person per database | — |
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
| Where the person says they put things ("I put my keys in the drawer") | IMPLEMENTED, TESTED | `conversational_memory` (`location:` facts) | C | `test_person_reported_location_is_remembered_and_updated`, `…camera_sighting_are_both_stated_newest_first` | Person's own report; MEMORA cannot verify it | — |
| Identity learning: consent at the storage layer; conflicting names never attributed | IMPLEMENTED, TESTED | `MemoraDatabase.add_evidence`, `identity_repository` | R | `test_identity_evidence_needs_consent_at_the_storage_layer`, `test_conflicting_introduction_creates_no_episode_under_the_confirmed_name` | A confirmed name is not changed by speech; correcting it needs a caregiver flow (not built) | — |
| Honest action boundaries (calls, messages, home devices, booking, reminders) | IMPLEMENTED, TESTED | `_capability_boundaries` | C | `test_requests_for_actions_memora_cannot_take_say_nothing_was_done` | Reminders only via `/add-medication`, `/add-appointment` | — |
| Object "last seen" with source and age | IMPLEMENTED, TESTED, SIMULATED | `conversational_memory`, `objects.source` | C/R | journeys `simulated_object_observation`, `stale_object_observation`; `test_observation_provenance_is_stated` | Real detection is a contour heuristic (experimental) | Licence-compatible detector |
| Schema migrations | IMPLEMENTED, TESTED | `src/memory/migrations.py` | automatic | `test_migrations.py` incl. copy of the local DB | Additive only | — |
| Persistence across restart | IMPLEMENTED, TESTED | SQLite + per-DB embeddings | C | journey `restart_persistence`; Docker CI job | — | — |
| View / export / delete (incl. logs) | IMPLEMENTED, TESTED | `user_data.py`, chat | C | `test_chat_and_user_data.py`, `test_failure_handling_and_deletion.py`, journey `export_and_delete`, `test_export_contains_every_stored_personal_row` | Backups are not deleted (the person is told); no secure erase | — |
| Backup / restore (incl. corrupt live DB) | IMPLEMENTED, TESTED | `src/memory/backup.py` | `--backup`, `--restore` | `test_backup_restore.py` (incl. manifest path validation), journey `backup_and_corruption_recovery`, `test_cli_end_to_end.py` | Stop MEMORA before restoring | — |
| Storage-failure handling | IMPLEMENTED, TESTED | `open_user_database` | C/R | `test_failure_handling_and_deletion.py` (real CLI subprocess) | — | — |
| Repair of faceless identities | IMPLEMENTED, TESTED | `--repair` | `--repair` | tests on copies | — | Owner decision for the local DB |
| Simulation (clock, battery, sensor failure, journeys) | IMPLEMENTED, TESTED, SIMULATED | `src/simulation/` | S | `test_simulation_journeys.py` (20 journeys + runner meta-tests) | Simulated only | — |
| Runtime status / diagnostics (`--check` read-only) | IMPLEMENTED, TESTED | `AnchorRuntime.get_subsystem_statuses`, `--check` | K/R | `test_honest_runtime_reporting.py`, journey `sensor_unavailable`, `test_check_never_modifies_or_creates_the_user_database`, `test_media_library_isolation.py` | — | — |
| No physical devices in tests | IMPLEMENTED, TESTED | `tests/conftest.py` guard | — | `test_no_physical_devices.py` | — | — |
| Real devices only via `--live-hardware` | IMPLEMENTED, TESTED | `factory.hardware_config_for`, coordinator/pipeline defaults, `--vision-standalone` gate | all | `test_hardware_activation_is_explicit.py` (23 cases, every `MEMORA_PROFILE` value) | — | — |
| Network policy (no outbound connection unless opted in) | IMPLEMENTED, TESTED | `src/network_policy.py`; lazy, local-only model loading | C/S/R/K | `test_network_policy.py` (socket interception); `--check` "Network Use" | Opt-in paths (downloads, cloud ASR, Gemini) not exercised against live services | — |
| Simulation isolation | IMPLEMENTED, TESTED | `app.py --simulate` workspace | S | `test_simulation_isolation.py`; real environment unchanged after 20/20 | — | — |
| End-to-end text product via CLI | TESTED | `app.py --chat/--backup/--check/--restore` | C | `test_cli_end_to_end.py` | Synthetic data only | Owner dogfooding |
| Stability | SIMULATED | soak harness | `deployment/benchmarks/soak_runtime.py` | `docs/evidence/` (10–20 min soaks) | ≤ 20 min, simulated | Multi-hour soak; real hardware |
| Clean development database | IMPLEMENTED, TESTED | `deployment/create_dev_database.py` | — | `test_create_dev_database.py` | — | — |
| Camera, microphone, ASR, TTS | HARDWARE-UNVERIFIED | `src/runtime/*_adapter.py` | R `--live-hardware` | none on real devices (tests block real devices) | Never run on hardware in this work | Owner authorisation for device testing |
| Face recognition (real faces) | **NOT WORKING**, BLOCKED (backend + licensing) | `face_recognizer.py` | R | `test_live_recognizer_without_a_working_backend_detects_nothing` | With `requirements-hardware.txt` no backend works (dlib not installed; the InsightFace backend was never implemented; MediaPipe 0.10.35 lacks FaceMesh). The recogniser now reports `FAILED (<reason>)` instead of fabricating faces (`b00922f`) | Owner decision D3 (`docs/LICENSING_REVIEW.md`), then hardware test |
| Object detection (real) | HARDWARE-UNVERIFIED, BLOCKED (licensing for YOLO) | `object_detector.py`, `object_ledger.py` | R | none | Contour heuristic; YOLO is AGPL-3.0 | Replace or license |
| Gemini name extraction | EXTERNALLY-UNVERIFIED | `context_binder.py` | R (identity learning) | fake-client tests | No key; API terms need review | Owner-provided test key |
| Dashboard (developer view) | IMPLEMENTED, TESTED (browser, synthetic events) | `experience/` | `--dashboard` | browser check with hostile input | Telemetry view, not a carer product | — |
| Docker deployment | IMPLEMENTED, TESTED | `deployment/docker/Dockerfile` | docker | local runs + CI Docker job | Core text mode only | — |
| Clean install / CI | IMPLEMENTED, TESTED | `requirements*.txt`, `.github/workflows/ci.yml` | — | `09cf8ac`: fresh clone 3.11 808 passed / 4 skipped; clean 3.12/3.13 containers 806 passed / 6 skipped; CI matrix 3.11/3.12/3.13 + Docker green | Microphone capture (optional SpeechRecognition) does not support 3.13 | — |
| Platforms | — | — | — | macOS arm64 (native), Linux arm64 (Docker), Linux x86-64 (CI) | Windows, Raspberry Pi, wearables untested | — |
