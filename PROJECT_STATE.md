# MEMORA — Project State

_Last updated: 2026-10-21. This file records verified facts only. Where something
was not run or not checked, it says so._

## 0. Current state — face-recognition and release-blocker mission (2026-10-21)

**Git:** branch `fix/p0-data-isolation-and-safety`, pushed; no force-pushes or history
rewrites; draft PR #1 open, not merged. Final product code `7c96988`; later commits are
documentation only. 16 untracked owner files (`validation/artifacts/session_*`) untouched.

**Done in this mission** (`docs/EXECUTION_LEDGER.md` G-01…G-08):
| Commit | Change |
| :--- | :--- |
| `6cf2032` | Database incident verified read-only; recovery decision record (`docs/DATABASE_INCIDENT_RECORD.md`) |
| `7346491` | OpenCV YuNet + SFace face-recognition backend: pinned checksums, owner provisioning, no download, consent before any embedding, ambiguity → "Not sure who this is", no duplicate enrolment; inactive until models are provisioned (`docs/FACE_RECOGNITION.md`) |
| `067f92d` | Docker image on headless OpenCV (no Qt, no `libavdevice`); licence notices and CycloneDX SBOM generated at build |
| `b1028dc` | Voice path: odd-length audio no longer crashes or is dropped; speech-recognition availability in the runtime status |
| `5c4fdf6` | Face-consent revocation states that stored face data is kept; adversarial journey tests |
| `7c96988` | `/delete-all` names export files that still hold the person's data |

**Verified:** see `docs/RELEASE_GATES.md` (dev suite 868 passed; clean 3.11 863 / 4 skipped;
clean 3.12 and 3.13 861 / 6 skipped; journeys 20/20; Docker contents and persistence; CI on the
final commit in PR #1).

**Database (F-04):** the live `memora_db_v2.sqlite` is still in its migrated state (SHA-1
`972ed943…`). The pre-incident copy is byte-identical to the original (SHA-1 `26f38093…`,
matched by four independent copies), and the 29 Sep backup is unchanged. Nothing was
restored; options and the exact procedure are in `docs/DATABASE_INCIDENT_RECORD.md`.

**Face recognition:** implemented and tested with synthetic stand-ins. **Not active**: no
model files are shipped, downloaded or provisioned. **Never tested** with real model files or
a camera.

**Not verified:** every real device path; Windows; live Gemini; R-09 on macOS; runs longer
than 20 minutes.

**Owner decisions:** see `docs/RELEASE_GATES.md` §5 (prioritised).

Software completion is not release authorisation.

### Earlier: final handoff audit at `fafcb78` (2026-10-20)
CI and local suite green (756 passed); found C2-19…C2-24, all except C2-24 (owner decision)
fixed in the mission above.

## 1. Repository and branches

| Item | State |
| :--- | :--- |
| Remote | `git@github.com:AayushAade/Samsung_Anchor.git` (push over SSH verified). **Repository visibility: PUBLIC** (checked with `gh`, 2026-10-20) |
| Integration branch | `main` (`0c0c6a0`, "Merge branch 'release/rc1'") |
| Active work branch | `fix/p0-data-isolation-and-safety` (pushed) — based on `feature/interactive-demo` |
| Other branches | `feature/context-fusion`, `feature/memory-foundation`, `feature/prediction-intelligence`, `feature/realtime-runtime`, `release/rc1`, `origin/project-restructure`: **all are ancestors of `feature/interactive-demo`** (no unmerged work found) |
| Pre-existing uncommitted work | 22 modified + 9 untracked files (Phase 9–11 executive/cognitive work) were preserved as commit `5ebaa1e` on `chore/checkpoint-phase9-11-wip` (local) and are included in the work branch. Not reviewed line-by-line. |
| Local user data | `memora_db_v2.sqlite` (git-ignored). Backed up to `~/memora_backups/20261020/` before any work. Checksum unchanged by all test runs after commit `0b9d3f6`. |

Commits on the work branch (newest first):

| Commit | Summary |
| :--- | :--- |
| `6bd49a9`, `5adcb76`, `175f3c3` | Soak evidence; release gates; architecture/roadmap/ledger refresh |
| `e4dc941` | Dashboard WebSocket origin allow-list (cross-site hijacking) |
| `ac87a0f`, `592ddab` | No silent cloud transcription; voice consent; Python 3.12/3.13 core verified |
| `466be66` | Suite can never touch physical devices or make sound; honest speaker fallback; licensing + safety docs |
| `8c671ec` | GitHub Actions CI (tests, ruff, journeys, diagnostics, Docker) — **4/4 checks passing** |
| `0666d05` | Simulation: clock, battery, sensor failures, 20 journeys; fixed restore-on-corrupt and thread leak |
| `8313383` | Versioned additive migrations; object sightings record and state their source |
| `1bc192a` | Actionable storage errors; delete-all removes logs and session state |
| `e5fbee3` | Consent enforced (storage + face recognition); consent onboarding |
| `cef558c`, `bbca359` | Conflicting relations, corrections, retraction, pronouns, names (bbca359 fixes a test committed red in cef558c) |
| `3354043` | Response guard on the delivery path; honest call/medication/diagnosis answers |
| `cdd1465` | Phrasing corpus (40 cases via pipeline): 32/40 → 40/40 |
| `44f385f` | Configurable emergency number and trusted contact in urgent guidance |
| `839ea7b` | Fictional people/prescriptions/habits removed from all real-use components (object-graph sweep test) |
| `1abc9ed` | Dashboard escaping verified in browser; no invented routine, escalation, consent, confidence |
| `8777df7` | Docs refresh |
| `17ba5ed` | Runtime soak harness + before/after evidence (`docs/evidence/`) |
| `4bd4968` | Logging with rotation (0600 log); per-cycle diagnostics off the console; `--verbose` |
| `609d2e8` | Bounded per-track face-embedding history (unbounded growth found by soak) |
| `87f6e94` | Own turns attributed to the person, not "Eleanor"; own turns are not "visits" |
| `ecec514` | Dashboard: no fictional defaults; "no data" never shown as "meds confirmed" |
| `34ef886` | Runtime NameErrors found by ruff fixed; bug-focused `ruff.toml` gate |
| `4695a8a` | `--backup` / `--restore` with checksums and pre-restore copy |
| `f4d1cd9` | Persisted medication schedules/appointments; reported (not verified) doses; truthful audit |
| `e2b97f3` | 0600 data files; `--repair`; MEMORA's own replies no longer stored as memories |
| `d2ad57c` | Source-of-truth documents |
| `9f47497` | Scenario harness compares actual vs expected; fixes for defects it exposed |
| `823a85e` | Reproducible install, working container, `--check`, hardened Gemini path |
| `85134ff` | `--chat` text conversation mode with view/correct/export/delete controls |
| `90eab3c` | Honest runtime status/telemetry; no double speech; **commit 9 never-tracked `src/runtime/` modules** |
| `cdddbba` | Conversational memory rework (facts, corrections, names, orientation, objects) |
| `00160c6` | Urgent-safety routing; demo data removed from live paths |
| `0b9d3f6` | Per-database face-embedding storage; tests isolated from user data |
| `5ebaa1e` | Checkpoint of pre-existing uncommitted work |

Correction: the message of `823a85e` states "640 passed"; that run printed 636.

## 2. Environment (as used for verification)

- macOS 27.0, arm64; Python 3.11.15 (`.venv`).
- Docker 29.5.2 (linux/aarch64) available and used.
- No `GEMINI_API_KEY` configured → cloud paths not exercised against the live API.
- No camera or microphone was opened during this work (privacy; not needed for the verified paths).
- `assets/models/` contains `scrfd_500m_bnkps.onnx` (tracked). `yolov8n.pt` exists locally (ignored).
- Real data, verified unchanged at the end of the 2026-10-21 mission: `memora_db_v2.sqlite` SHA-1 `26f38093…`; `~/memora_backups/20261020/memora_db_v2.sqlite` SHA-1 `d8d8ccd7…`.

## 3. Verified entry points

| Command | Verified result |
| :--- | :--- |
| `python app.py --chat` | Onboarding, fact storage, recall after restart, urgent guidance, `/memories`, `/forget`, `/export`, `/delete-all` — verified via piped sessions and `tests/test_chat_and_user_data.py` |
| `python app.py --check` | Diagnostics incl. user-DB integrity; flags the local DB's 27 identities without face data |
| `python app.py --simulation --validate-runtime --max-cycles N` | Runs, exit 0; uses `data/simulation/` DB; measured report |
| `python app.py --scenario` | 11/11 against specifications (harness now compares actual vs expected) |
| `python inspect_database.py [path]` | Reports tables and SQLite↔embedding inconsistencies |
| `python app.py --backup [DIR]` / `--restore DIR` | Verified on a copy of the local DB: backup → delete all episodes → restore recovered 131/131 |
| `python app.py --repair` | Verified on a copy: 27 faceless identities removed after typed confirmation; episodes kept. **Not run on the real DB** (owner decision) |
| Chat care commands (`/add-medication`, `/appointments`, …) | Verified across restart; `tests/test_care_schedules.py` |
| `python deployment/benchmarks/soak_runtime.py SECONDS` | 20 min and 10 min simulated soaks run; see `docs/evidence/RUNTIME_SOAK_20261020.md` |
| `docker build -f deployment/docker/Dockerfile .` + `docker run -it -v memora-data:/data memora` | Built and run; `--check` passes with optional-capability warning; chat memory persisted across two container runs |
| Dashboard (`experience/server.py`) | Run against synthetic events in the browser pane: escaping and honest fallbacks verified (`1abc9ed`) |
| `python app.py` (no args) | Simulated runtime (real devices only with `--live-hardware`) |
| `--live-hardware`, `--vision-standalone --live-hardware` | **Not run** in this work (would open camera/microphone). Without `--live-hardware`, `--vision-standalone` exits 2 (tested) |
| `demo_mode.py`, `operate.py --demo` | Scripted presentation — output is labelled synthetic |
| `demo.py`, `live_demo.py`, `demo_experience.py`, `identity_learning_demo.py` | Not reviewed or run |

## 4. Test baseline

| When | Environment | Result |
| :--- | :--- | :--- |
| Start of work (`5ebaa1e`) | `.venv` | 538 passed in 51 s — **but the suite modified the real user DB and wrote into the repo** |
| `9f47497` | `.venv` | 641 passed in 58 s; real DB checksum unchanged; no repo files modified |
| `17ba5ed` | `.venv` | 658 passed in ~60 s; `ruff check .` (E9/F63/F7/F82) clean |
| `cdd1465` | `.venv` | 666 passed in ~64 s; ruff gate clean |
| `8ccf2bd` | fresh clone, clean venv (core+dev) | 664 passed, 2 skipped (cloud SDK not installed), 21 s |
| `466be66` | `.venv` (macOS arm64) | 749 passed in ~73 s; ruff clean; `app.py --simulate` 20/20 |
| `ac87a0f` | clean `python:3.12-slim` and `python:3.13-slim` containers | 747 passed, 6 skipped (reasons stated); journeys 20/20 |
| **Latest (`2990621`, product code)** | `.venv`; fresh clone + clean 3.11 venv; clean 3.12/3.13 containers | **840 passed**; 836 passed / 4 skipped; 834 passed / 6 skipped each — see `docs/RELEASE_GATES.md` |
| `09cf8ac` | same environments + GitHub Actions | 812 passed; 808 / 4 skipped; 806 / 6 skipped; CI green |
| `6bd49a9` | fresh clone, clean Python 3.11 venv, core+dev deps | **752 passed, 4 skipped** (reasons stated), 23 s; ruff clean; journeys 20/20; `--check` pass; chat verified |
| `6bd49a9` | GitHub Actions (ubuntu, Python 3.11) | core and Docker jobs passing on push and PR |
| `466be66` | GitHub Actions, ubuntu-latest, Python 3.11 | core job (ruff, pytest, journeys, --check) and Docker job passing |
| `823a85e`-era | Fresh clone + clean venv, `requirements-dev.txt` only | 634 passed, 2 skipped (cloud SDK not installed) |
| Before `90eab3c` | Fresh clone | **Import failure**: `src/runtime/runtime_engine.py` had never been committed |

Static analysis: `ruff.toml` (correctness rules only) passes; it found three
runtime NameErrors that were fixed. No type checking is configured. CI:
`.github/workflows/ci.yml` (GitHub-hosted runners, free for this public repository) runs
ruff, the suite, journeys and `--check` on Python 3.11/3.12/3.13, plus a Docker job.

## 5. Known blockers and open issues

- **Local database (2026-10-21):** migrated by the F-04 incident (rows unchanged; pre-incident copy secured; see §0).
- **Local database: what it contains (read-only inspection, 2026-10-20).** Episodes 3 Aug (81),
  4 Aug (30), 29 Sep (10), 20 Oct (10), all for "Eleanor" (fictional demo patient) or "Sid";
  27 identities (1 named, "Sid"; none have face data); 7 memory rows (one overwritten by the old
  fixed-"temp"-id bug); 2 object sightings that are simulation seeds. No evidence of genuine
  personal use. The pre-work backup (`~/memora_backups/20261020/`, 29 Sep state) differs only by
  the 20 Oct test-run additions. Until 2026-10-21 06:01 the file had never been opened by the new code (see F-04).
- **Safe procedure for a clean development database** (tool `deployment/create_dev_database.py`,
  tested by `tests/test_create_dev_database.py`; demonstrated 2026-10-21 in a temporary folder:
  created, `--check` "0 people, consistent", chat, verified backup):
  1. `python deployment/create_dev_database.py ~/memora-data/dev`. The tool refuses an existing
     database and the project-folder default, then verifies schema version 1, zero personal rows
     and mode 0600.
  2. Export the two variables it prints (`MEMORA_DB_PATH`, `MEMORA_LOG_DIR`) in every shell
     used for MEMORA work. Without them, commands use `memora_db_v2.sqlite` in the project folder.
  3. `python app.py --check`, `python app.py --chat`, then `python app.py --backup ~/memora-data/dev/backups`.
  `--check` is read-only since `5f753f6` (it inspects a temporary copy); `--chat`, the runtime
  and `--restore` still write to whichever database is configured.
- **Local database contamination (owner action).** `memora_db_v2.sqlite` was written to by
  earlier test runs before tests were isolated: the "Reading Glasses"/"Water Bottle" sightings
  are simulation seeds (present in the 20 Oct pre-work backup from 29 Sept), and 10 episodes plus
  1 identity were added by the first baseline run of this work (15:15 on 20 Oct). MEMORA now
  presents legacy sightings as unverified notes. Options: restore
  `~/memora_backups/20261020/memora_db_v2.sqlite`, or start a fresh database for real use.

- Real hardware paths (camera, microphone, TTS, face recognition, object detection) are **unverified**.
- Gemini integration is unverified against the live API (no key).
- 27 identities in the local DB have no face embeddings (lost to the pre-fix shared-index defect). `python app.py --backup` then `python app.py --repair` will remove them after confirmation; not run on the real DB.
- The repository is public: the tracked InsightFace model is being redistributed publicly, and public disclosure may affect any future patent filing (see `docs/LICENSING_REVIEW.md`, `docs/product/PRODUCT_SPEC.md`).
- Licensing: no repository LICENSE; AGPL-3.0 (Ultralytics) and a tracked InsightFace model need review before any commercial use. See `docs/LICENSING_REVIEW.md`.
- Many legacy documents (README badges, `docs/certification/*`) claim certification/production readiness that is not supported by evidence. See section 6.

## 6. Documentation status index

| Document | Status |
| :--- | :--- |
| `PROJECT_STATE.md`, `SYSTEM_ARCHITECTURE.md`, `CAPABILITY_VERIFICATION_MATRIX.md`, `MASTER_ROADMAP.md`, `docs/LICENSING_REVIEW.md` | **Current** (this work) |
| `README.md` | Current (rewritten in this work) |
| `docs/RELEASE_GATES.md`, `docs/EXECUTION_LEDGER.md`, `docs/PRIVACY_AND_CONSENT.md`, `docs/SAFETY_AND_LIMITATIONS.md` | **Current** |
| `docs/HARDWARE_TEST_CHECKLIST.md`, `docs/PILOT_CHECKLIST.md` | **Current, prepared but not executed** |
| `docs/DATABASE_INCIDENT_RECORD.md`, `docs/FACE_RECOGNITION.md` | **Current** |
| `docs/certification/*` (RC1 certification, safety certification, production readiness, final engineering review) | **Historical / unsupported.** Written before this audit; claims (e.g. "479 passing", "ARCHITECTURE CERTIFIED", safety certification) were not reproducible: the suite could not run from a clean clone, the scenario validator never compared results, and safety behaviour was defective. Do not cite. |
| `docs/clinical/clinical_evaluation_report.md` | Synthetic demo output (now labelled). Not clinical evidence. |
| `deployment/deployment_guide.md`, `docs/DEPLOYMENT_GUIDE.md`, `docs/OPERATIONS_MANUAL.md` | Historical; not re-verified. Use README quick start. |
| `docs/ARCHITECTURE_GUIDE.md`, `docs/architecture*`, `docs/system_architecture.md` | Historical design intent; `SYSTEM_ARCHITECTURE.md` describes code as it runs today |
| `RELEASE_NOTES.md`, `CHANGELOG.md` | Historical |

## 7. Most recent verified milestone

Core text-based product loop (talk → remember → recall after restart → inspect /
correct / export / delete), person-entered medication schedules and appointments
with reported-dose tracking and throttled reminders, backup/restore, and honest
safety behaviour work end to end on macOS and in a Linux container from a clean
install. Simulated runtime is stable over a 10-minute soak after the track fix.
