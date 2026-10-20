# Execution Ledger

Persistent record of findings and work in progress, so an interrupted session
does not repeat work. Newest cycle first. Severity: P0 safety/data/privacy,
P1 core product, P2 reliability, P3 usability/commercial.

## Cycle 2 — started 2026-10-20 (branch `fix/p0-data-isolation-and-safety`, PR #1 draft)

Phase Zero (verified): branch == origin (0/0); no other branch has unique commits;
PR #1 open, draft, mergeable, 0 reviews; working tree clean except owner's untracked
`validation/artifacts/session_*` files (left untouched); real DB checksum
`26f38093…` unchanged.

| ID | Sev | Finding | Evidence | Status | Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| C2-01 | — | Fresh-clone baseline at 8ccf2bd (clean venv, core+dev deps) | 664 passed, 2 skipped (cloud SDK absent), 21 s; ruff clean | done | — |
| C2-02 | P0 | "Did you call my daughter?"/"Call my daughter" got generic fallback; medication-change and diagnosis questions unhandled ("Can I stop taking my medicine?" -> object lookup) | probe via pipeline | fixed `3354043` | test_response_guard_and_boundaries |
| C2-03 | P0 | No safety check on the live output path (SafetyManager audit-only) | code trace | fixed `3354043`: response_guard on delivery | test_guard_runs_on_delivery_path |
| C2-04 | P1 | Second daughter replaced first; "my daughter is not Riya" would store name "not riya"; "I like it" stored; "your them"; no name questions / forget | probe | fixed `cef558c` (+`bbca359` corpus expectation fix; cef558c was committed with a failing corpus test — process error, gate now on pytest exit status) | test_conversational_memory, corpus |
| C2-05 | P0 | Consent never enforced: facts/episodes always stored; live recogniser enrolled faces without consent | code trace | fixed `e5fbee3` | test_consent_enforcement |
| C2-06 | P2 | Corrupt/unwritable DB -> raw traceback | CLI run | fixed `1bc192a` | test_failure_handling_and_deletion |
| C2-07 | P0 | /delete-all left utterances in log files and session memory | code trace | fixed `1bc192a` | same |
| C2-08 | P2 | SpeechRecognition (core dep) imports aifc/audioop removed in Python 3.13 | DeprecationWarning | fixed `592ddab` (optional), `ac87a0f`; core verified on 3.12/3.13 containers | containers |
| C2-09 | P1 | Simulation: no battery/sensor-failure simulation, controlled clock, journey runner | audit | done `0666d05` (20 journeys) | test_simulation_journeys |
| C2-10 | P0 | restore_backup failed when the live DB was corrupt | journey | fixed `0666d05` | test_restore_works_when_live_database_is_corrupt |
| C2-11 | P2 | Context-fusion thread pool leaked per pipeline (restarts, /delete-all) | journey + thread trace | fixed `0666d05` | journey extended_operation |
| C2-12 | P0 | Test suite drove real devices on the Mac: pyttsx3 speech, `say`, camera index 0-3 probe, default mic | CI failure on Linux | fixed `466be66` (suite-wide guard) | test_no_physical_devices |
| C2-13 | P1 | Hardware speaker reported success when nothing was spoken | code | fixed `466be66` | test_speaker_without_audio_backend_reports_failure |
| C2-14 | P0 | Identity learning sent microphone audio to Google (recognize_google) with no consent/disclosure | code trace | fixed `592ddab` | test_cloud_asr_and_voice_consent |
| C2-15 | P2 | Deployment validator required speech_recognition and pytest | py3.13 container | fixed `ac87a0f` | test_trust_and_safety |
| C2-16 | — | Local DB contains test-run contamination (sim seeds, 10 test episodes, 1 identity) | read-only comparison with backup | owner decision; documented | — |
| C2-17 | P3 | Object sighting source; schema migrations | audit | done `8313383` | test_migrations |
| C2-18 | P2 | CI | — | done `8c671ec`; green on `466be66` | GitHub Actions |

### Final handoff audit at `fafcb78` (2026-10-20) — findings recorded, **not fixed** (audit-only scope)
| ID | Sev | Finding | Evidence | Recommended fix |
| :--- | :--- | :--- | :--- | :--- |
| C2-19 | P1 | With storage consent **declined**, "I took my aspirin" still stores a REPORTED_TAKEN care event and replies "I've noted…", contradicting "I won't save anything you tell me" | probe in temp dir: `care_events=1` after declining | Gate `_medication_report` on `_may_store()`; reply that memory is off |
| C2-20 | P2 | Explicit commands (`/add-medication`, `/add-appointment`, `/set-emergency-number`, `/set-trusted-contact`) save regardless of storage consent; replies say "Saved" but the policy is undocumented | same probe: `care_items=1` | Owner/product decision; then document or gate |
| C2-21 | P2 | `app.py --simulate` appends INFO metadata (temp DB paths, migrations applied) to the real `data/logs/memora.log`; no conversation content | real log grew 1,820 → 16,651 bytes; only `src.memory.*` and `httpx` lines | Configure logging into the journey temp dir (or disable file logging) in `--simulate` |
| C2-22 | P1 | When `faster-whisper` (hardware extra) is installed, every pipeline start makes an HTTPS request to huggingface.co for `Systran/faster-whisper-tiny.en` (and downloads it if absent). Chat says "Nothing is sent anywhere" | 27 `httpx` GETs during `--simulate`; 1 per chat start. Core install / Docker / CI do not include faster-whisper | Load ASR lazily only in voice mode; `local_files_only`/offline by default; disclose any download |
| C2-23 | P1 | Chat and `--simulate` use simulated adapters only because `MEMORA_PROFILE` is unset; with a hardware profile (e.g. `LAPTOP`) they would construct real camera/microphone adapters | `ConfigManager().get_runtime_mode()` → LAPTOP when set; pipeline takes mode from it regardless of `live_hardware=False` | Force `RuntimeMode.SIMULATION` when `live_hardware is False` |
| C2-24 | info | Local `memora_db_v2.sqlite` has never been opened by the new code (no `schema_version`, no `source` column, 0644). `--check`, `--chat` and the runtime would migrate it and set 0600; `--backup` only reads it | read-only `sqlite3` inspection; checksum `26f38093…` unchanged | Follow the clean-DB procedure in PROJECT_STATE §5 |

## Cycle 1 — 2026-10-20 (commits 5ebaa1e..8ccf2bd)
See PROJECT_STATE.md commit table and MASTER_ROADMAP.md "Done in this cycle".
