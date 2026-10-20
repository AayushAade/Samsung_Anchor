# MEMORA — Capability Verification Matrix

_2026-10-20. Evidence levels: **U** unit test · **I** integration test through the real
pipeline/DB · **E** end-to-end run of a user entry point · **S** simulated only ·
**—** none. No capability has physical-world or clinical evidence._

| Capability | Implementation | Evidence | Prerequisites | Status / limitations |
| :--- | :--- | :--- | :--- | :--- |
| Text conversation | `src/application/chat.py`, `app.py --chat` | E (piped sessions, macOS + container), I `tests/test_chat_and_user_data.py` | core deps | **Verified.** Rule-based; understands a bounded set of phrasings |
| Remember user facts with provenance | `src/cognition/conversational_memory.py` | U/I `test_conversational_memory.py`, `test_pipeline_conversation_correctness.py` | — | **Verified.** likes/dislikes, preferences, favourites, relations |
| Topic-relevant recall with attribution | same | U/I | — | **Verified.** Unrelated facts are not offered; "don't have a record" otherwise |
| Corrections / supersession with history | same | U/I | — | **Verified.** Old fact kept as superseded; person told what changed |
| Persistence across restart | SQLite + per-DB embeddings | I (restart tests), E (chat across processes and container runs) | writable DB path | **Verified** |
| Preferred name onboarding | `ConversationalMemory._name_introduction` | U/I/E | — | **Verified.** "I'm tired" etc. never taken as names |
| Orientation (time/date) | same | U/I, scenario CS-05 | system clock | **Verified** (clock only; location is never guessed) |
| Object "last seen" answers | same + `ObjectRepository` | U/I | real observations | Logic **verified** with logged observations. Real object detection **unverified** (see below) |
| Urgent-situation guidance | `src/clinical/urgent_safety.py`, patient state, care policy | U/I `test_urgent_safety.py` (30 cases), scenario CS-08 | — | **Verified** for the listed phrasings. Rule-based, English only, not a validated triage tool. MEMORA cannot contact anyone and says so |
| Scheduled medication reminders | `MedicationManager`, pipeline throttle | U/I `test_medication_manager.py`, `test_scenario_validator_honesty.py`, CS-04 | schedules must be configured | Logic **verified**. **No way for a user to enter schedules; not persisted.** Never infers a dose was taken |
| Appointments | `AppointmentManager`, `ConversationalMemory._appointment` | I (CS-03) | appointments must be configured | Answers "none recorded" honestly; **no entry UI; not persisted** |
| Known-visitor announcement | pipeline `_is_known_visitor_arrival` | I CS-11, `test_scenario_validator_honesty.py` | named identity + real recognition | Logic **verified** with synthetic recognition results |
| Face recognition | `src/vision/face_recognizer.py` (dlib/insightface/mediapipe fallbacks) | S only (mock embeddings) | camera, models | **Unverified** on real faces |
| Face-embedding store integrity | `src/memory/vector_store.py`, `check_integrity()` | U/I `test_data_isolation_and_integrity.py` | — | **Verified**: isolation, restart, corruption quarantine, rollback, deletion |
| Object detection | `src/perception/object_detector.py` | S | camera | Live path is an OpenCV contour heuristic, not a trained detector — **experimental/unverified**. YOLO ledger exists separately (AGPL) and is not on the main path |
| Microphone + speech-to-text | `microphone_adapter.py`, `speech_recognition_engine.py`, `audio_listener.py` | S | mic, faster-whisper / SpeechRecognition | **Unverified** |
| Voice output | `speaker_adapter.py` (pyttsx3) | S (console) | audio device | **Unverified** on hardware; double-speech defect fixed |
| Camera capture | `camera_adapter.py` | — | camera | **Not run** in this work |
| Simulation mode | simulated adapters, `--simulation` | E | — | **Verified**; separate DB; simulated detections never persisted; status shows "Simulated" |
| Runtime status / diagnostics | `AnchorRuntime.get_subsystem_statuses`, `RuntimeManager.generate_diagnostic_report`, `--check` | I `test_honest_runtime_reporting.py`, E | — | **Verified** not to claim READY without a check |
| Runtime stability (long duration) | `--validate-runtime` | E (3–5 cycles only) | — | **Not established.** No long-duration run performed |
| View / export / delete user data | `src/memory/user_data.py`, chat commands | I `test_chat_and_user_data.py` | — | **Verified**; deletion recounted; export 0600, no raw embeddings |
| Cloud reasoning (Gemini) | `src/reasoning/context_binder.py` | U with fake client | key + network | Request/validation path tested offline; **live API unverified**. Replies never use an LLM |
| Clinical scenario harness | `src/clinical/scenario_validator.py`, `--scenario` | I (11/11 + harness-failure test) | — | **Verified harness**; scenarios are synthetic, not clinical evidence |
| Dashboard | `experience/server.py`, `--dashboard` | — | browser | **Not run**; still has an "Eleanor" placeholder default in `app.js` |
| Caregiver features (reports, escalation policies, FHIR/HL7 adapters) | `src/caregiver/`, `src/interoperability/` | unit tests from earlier phases (not re-reviewed) | — | **Not reviewed**; no notification channel exists |
| Container deployment | `deployment/docker/Dockerfile` | E (Docker 29.5, linux/aarch64) | Docker | **Verified** for core text mode |
| Clean install | `requirements*.txt` | E (fresh clone + clean venv: 634 passed, 2 skipped) | Python 3.11 | **Verified** on macOS arm64; other platforms untested |
| Platforms | — | macOS arm64 (native), Linux arm64 (container) | — | Windows, x86-64 Linux, Raspberry Pi, wearables, glasses: **untested** |
