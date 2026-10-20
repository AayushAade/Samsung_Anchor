# MEMORA — System Architecture (as implemented)

_Updated 2026-10-21 (consent policy, explicit hardware activation, network policy, simulation isolation). Describes the code paths that actually execute today, traced from
`app.py`. Design intent from older documents is not repeated unless the code
implements it._

## 1. System boundary

MEMORA is a single Python process. It has no server API, no accounts, and no
network dependency for its core loop. **Network policy** (`src/network_policy.py`): no outbound
connection unless an opt-in variable is "1" — `MEMORA_ALLOW_MODEL_DOWNLOAD` (model weights),
`MEMORA_ALLOW_CLOUD_ASR` (Google speech recognition), `MEMORA_ALLOW_CLOUD_LLM` + `GEMINI_API_KEY`
(Gemini name extraction); models otherwise load from local files only, and speech recognition
loads lazily on first use. The only listener is the optional local dashboard (`--dashboard`,
localhost:8765, origin allow-list).

**Hardware activation** (`src/application/factory.hardware_config_for`): real camera,
microphone and speaker adapters are constructed only when `--live-hardware` is given;
otherwise every construction path (factory, coordinator, pipeline defaults) uses
`RuntimeMode.SIMULATION`, whatever `MEMORA_PROFILE` says. `--vision-standalone` also requires
`--live-hardware`.

**Consent policy** (`docs/PRIVACY_AND_CONSENT.md`): every persistent personal write requires
`memory` consent. User-facing paths refuse with an explanation, and the storage layer
(`CareStore`, `ConversationalMemory._save_fact`) raises `ConsentRequiredError` as a backstop.

```
 keyboard (--chat) ─┐
 camera frames ─────┤        ┌──────────────────────── process ───────────────────────┐
 microphone/ASR ────┼──────► │ AnchorRuntime ─► AnchorCoordinator ─► CognitivePipeline │ ──► speaker HAL (console / pyttsx3)
                    │        │                         │                    │          │
                    │        │                 identity learning     ConversationalMemory, safety,
                    │        │                 thread (+ optional    care policy, ~20 "phase" engines
                    │        │                 Gemini call)                 │          │
                    │        └──────────────────────────────────────────────┼──────────┘
                    │                                                       ▼
                    │                       SQLite DB (<name>_v2.sqlite) + face embeddings
                    │                       (<name>_v2.faces.json / .faces.index)
```

## 2. Entry points and modes

| Mode | Path | Database |
| :--- | :--- | :--- |
| `--chat` | `src/application/chat.py` → `build_application(live_hardware=False)` → `pipeline.process(user_speech=...)` per line. No runtime loop, no camera/mic. | `settings.DB_PATH` (default `memora_db_v2.sqlite`, override `MEMORA_DB_PATH`) |
| default / `--live-hardware` | `AnchorRuntime.run_continuous`: camera frame → recognizer → event bus → worker thread → pipeline | `settings.DB_PATH` |
| `--simulation`, `--scenario` | Same runtime with simulated adapters / scripted payloads | `data/simulation/memora_simulation_v2.sqlite` unless `MEMORA_DB_PATH` set |
| `--check` | `health_check.py` → `StartupValidator` (does not open camera) | `settings.DB_PATH` (opened for integrity check) |
| `--show-memory` | `inspect_database.inspect_database(None)` | `settings.DB_PATH` |
| `--simulate [NAME]` | `src/simulation/journeys.py`: each journey builds its own `ChatSession` with a `SimulatedClock` (and optional `SimulatedBattery`) | a fresh temporary directory per journey; the CLI also points `MEMORA_LOG_DIR`/`MEMORA_DB_PATH` at its own temporary workspace before logging starts, and removes it afterwards |
| `--backup [DIR]`, `--restore DIR`, `--repair` | `src/memory/backup.py`, `user_data.py` | `settings.DB_PATH` (opened via `open_user_database`) |

`build_application` (src/application/factory.py) is the single construction path
for all runtime modes.

## 3. Runtime and threading

- **Main thread**: `AnchorRuntime.run_continuous` loop (cycle delay 0.1 s) captures a
  frame, calls `AnchorCoordinator.process_frame`, drains the action queue, prints a
  heartbeat every 10 cycles.
- **Context-fusion pool**: each pipeline owns a 10-worker `ThreadPoolExecutor`; it is
  closed by `CognitivePipeline.shutdown()` (it previously leaked on every restart).
- **Cognitive worker thread** (daemon): `AnchorCoordinator._cognitive_worker_loop`
  consumes recognition results from a **bounded queue (max 10, drop-oldest,
  `dropped_events_count`)** and runs `CognitivePipeline.process`.
- **Action queue**: unbounded `queue.Queue`, drained every cycle by the main loop
  (speech is delivered inside the pipeline; the loop only drains).
- **Identity learning**: one background thread per unknown face
  (`src/integration/async_identity_learning.py`), with a 10 s per-face cooldown.
- **Speaker HAL**: `pyttsx3.runAndWait()` blocks the worker thread while speaking
  (real hardware only; simulated speaker prints).
- **Shutdown**: SIGINT/SIGTERM handler → `runtime.shutdown()` → coordinator joins the
  worker (2 s timeout) → pipeline shuts adapters. Not verified with real devices.

## 4. One cognitive cycle (`CognitivePipeline.process`)

Order of execution (src/pipeline/cognitive_pipeline.py):

1. Inject pending speech transcript; working-memory anaphora resolution.
2. Perception cycle (`PerceptionManager`). Detections are tagged
   `REAL_CAMERA` / `SIMULATED_CAMERA`; **only real-camera detections are persisted**.
3. Presence event (`PresenceEngine`); speech without a face creates a synthetic
   "self" event. No event → cycle ends.
4. Context fusion (identity, memory, temporal, continuity, social, assistance providers),
   goal inference, context restoration + attention, conversation manager.
5. Interaction manager proposes a presence greeting (discarded when the person spoke).
   Named known visitors are announced; unknown faces and the person themself are not.
6. Patient state (`PatientStateEvaluator`): emergency flag → **urgent concern in speech**
   (`src/clinical/urgent_safety.py`) → repetition/searching/disorientation/distress →
   overdue scheduled medication → oriented/calm.
7. Direct answer from `ConversationalMemory`: capability/medical boundaries first (calls,
   messages, medication changes, diagnosis), then names, orientation, forget/corrections,
   facts, medication reports/questions, appointments, timeline, visitors, objects (with
   sighting source and age), feelings, small talk. Returns nothing for urgent speech.
   Storing anything requires conversation-storage consent.
8. COS kernel + `SafetyManager.evaluate_action` — **recorded in the audit trail only;
   it does not gate what is spoken** (see §8).
9. Care policy (`CarePolicyFramework`) chooses principle and message.
10. **Reply precedence**: urgent guidance → direct answer → care-policy reply to speech →
    honest fallback; without speech: throttled scheduled reminder or visitor greeting.
10b. Battery notice (simulated battery only), never appended to urgent guidance.
10c. **Response guard** (`src/clinical/response_guard.py`) checks the final message for
    claims MEMORA cannot make (contacting anyone, doses taken, diagnoses, medication
    instructions) and replaces it if necessary.
11. Speak via `runtime_manager.speaker`; `last_speech_delivered` records the result
    (False if no audio backend actually spoke).
12. Persist: episode logged (only with storage consent). MEMORA's own replies are not
    stored as memories.
13. Decision trace, explainability, audit record (outcome SPOKEN / SPEECH_OUTPUT_FAILED / SILENT).
14. LTM, behaviour, reasoning, knowledge, executive, experience engines run and produce
    summaries — **after** the reply is spoken; their output goes to the cognitive stream /
    dashboard and does not influence the reply.
15. Emit `CognitiveStream` event (dashboard).

All exceptions inside the cycle are caught; `last_cycle_error` is set and the chat
front-end tells the person the turn may not have been saved.

## 5. Persistence

| Store | Location | Contents | Survives restart |
| :--- | :--- | :--- | :--- |
| SQLite (`MemoraDatabase`) | `<db>_v2.sqlite` | identities, identity_evidence, objects, object_history, episodes, relevant_memories (user facts with provenance tags; system replies), semantic_nodes, interaction_records, feedback_events, system_state (incl. preferred name) | Yes |
| Face embeddings (`FaissVectorStore`) | `<db>_v2.faces.json` (authoritative) + `.faces.index` (derived) | 128-D embeddings per identity | Yes; per database; atomic writes; corrupt files quarantined |
| SQLite care tables | `care_items`, `care_events` | medication schedules, appointments (with `entered_by`), REMINDED/REPORTED_TAKEN events | Yes |
| SQLite system_state | `system_state` | preferred name, emergency number, trusted contact, `consent:<feature>` decisions, `schema_version` | Yes |
| In-memory only | process | patient profile (demo defaults), caregiver preferences, working memory, search history, behaviour/executive state | **No** |

- `resolve_db_url` maps `memora_db.sqlite` → `memora_db_v2.sqlite` unless an existing file is passed explicitly.
- `MemoraDatabase.check_integrity()` cross-checks identities against embeddings.
- Schema: `create_all` creates missing tables; `src/memory/migrations.py` applies versioned,
  additive, transactional migrations (v1: `source` on `objects`/`object_history`) and refuses a
  database newer than the build. Structured fact fields are stored as tags.
- Database, face data, logs, exports and backups are written owner-only (0600 / 0700 dirs).
  Not encrypted at rest.

## 6. External dependencies and fallbacks

| Dependency | Used for | When missing |
| :--- | :--- | :--- |
| numpy, SQLAlchemy, faiss-cpu, OpenCV, SpeechRecognition, psutil, pydantic | core | import failure (required) |
| PyAudio / pyttsx3 / faster-whisper / insightface / mediapipe / ultralytics | real sensors and models | guarded imports; simulated/console fallbacks; `--check` reports missing packages |
| google-genai + `GEMINI_API_KEY` + `MEMORA_ALLOW_CLOUD_LLM=1` | identity-learning name extraction | local regex heuristics (default) |

## 7. Trust boundaries

- **User speech** (keyboard/ASR): parsed only by deterministic regex; never executed.
- **Microphone audio**: identity-learning transcription uses Google's online service; the
  microphone is not opened for it unless `MEMORA_ALLOW_CLOUD_ASR=1` and voice consent is given.
- **Dashboard**: localhost only; WebSocket accepts only the dashboard's own origin; all event
  text is HTML-escaped before rendering.
- **Gemini output**: untrusted; validated to a short plain name and a known relationship
  before it can label an identity; 10 s timeout; failures fall back locally.
- **Face recognition**: an identity is named only after it was bound via an explicit
  introduction or caregiver action; unknown faces are not named aloud.
- **Local files**: the database and embeddings are personal (biometric) data stored
  unencrypted on disk.

## 8. Known architectural limitations

- `SafetyManager` (cognitive OS) decisions are advisory/audit-only. Output safety is
  enforced by the urgent-safety path and the response guard on the delivery path.
- The ~20 "phase" engines run every cycle but do not affect behaviour; they add latency
  and complexity without user-visible effect.
- The patient profile (beyond preferred name and safety contacts) is not persisted.
- The pipeline prints extensively to stdout; `--chat` redirects it to `data/logs/chat_debug.log`.
- `CognitivePipeline.__init__` constructs every subsystem (~40 objects) eagerly; startup imports
  heavy optional ML packages when installed.
