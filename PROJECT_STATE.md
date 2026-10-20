# MEMORA — Project State

_Last updated: 2026-10-20. This file records verified facts only. Where something
was not run or not checked, it says so._

## 1. Repository and branches

| Item | State |
| :--- | :--- |
| Remote | `git@github.com:AayushAade/Samsung_Anchor.git` (push over SSH verified) |
| Integration branch | `main` (`0c0c6a0`, "Merge branch 'release/rc1'") |
| Active work branch | `fix/p0-data-isolation-and-safety` (pushed) — based on `feature/interactive-demo` |
| Other branches | `feature/context-fusion`, `feature/memory-foundation`, `feature/prediction-intelligence`, `feature/realtime-runtime`, `release/rc1`, `origin/project-restructure`: **all are ancestors of `feature/interactive-demo`** (no unmerged work found) |
| Pre-existing uncommitted work | 22 modified + 9 untracked files (Phase 9–11 executive/cognitive work) were preserved as commit `5ebaa1e` on `chore/checkpoint-phase9-11-wip` (local) and are included in the work branch. Not reviewed line-by-line. |
| Local user data | `memora_db_v2.sqlite` (git-ignored). Backed up to `~/memora_backups/20261020/` before any work. Checksum unchanged by all test runs after commit `0b9d3f6`. |

Commits on the work branch (newest first):

| Commit | Summary |
| :--- | :--- |
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

## 3. Verified entry points

| Command | Verified result |
| :--- | :--- |
| `python app.py --chat` | Onboarding, fact storage, recall after restart, urgent guidance, `/memories`, `/forget`, `/export`, `/delete-all` — verified via piped sessions and `tests/test_chat_and_user_data.py` |
| `python app.py --check` | Diagnostics incl. user-DB integrity; flags the local DB's 27 identities without face data |
| `python app.py --simulation --validate-runtime --max-cycles N` | Runs, exit 0; uses `data/simulation/` DB; measured report |
| `python app.py --scenario` | 11/11 against specifications (harness now compares actual vs expected) |
| `python inspect_database.py [path]` | Reports tables and SQLite↔embedding inconsistencies |
| `docker build -f deployment/docker/Dockerfile .` + `docker run -it -v memora-data:/data memora` | Built and run; `--check` passes with optional-capability warning; chat memory persisted across two container runs |
| `python app.py` (no args), `--live-hardware`, `--vision-standalone`, `--dashboard` | **Not run** in this work (would open camera/microphone/browser) |
| `demo_mode.py`, `operate.py --demo` | Scripted presentation — output is labelled synthetic |
| `demo.py`, `live_demo.py`, `demo_experience.py`, `identity_learning_demo.py` | Not reviewed or run |

## 4. Test baseline

| When | Environment | Result |
| :--- | :--- | :--- |
| Start of work (`5ebaa1e`) | `.venv` | 538 passed in 51 s — **but the suite modified the real user DB and wrote into the repo** |
| Latest (`9f47497`) | `.venv` | 641 passed in 58 s; real DB checksum unchanged; no repo files modified |
| `823a85e`-era | Fresh clone + clean venv, `requirements-dev.txt` only | 634 passed, 2 skipped (cloud SDK not installed) |
| Before `90eab3c` | Fresh clone | **Import failure**: `src/runtime/runtime_engine.py` had never been committed |

There is no linting/type-checking configured and none was run. No CI is active
(`deployment/ci/github-workflow.yml` is a template).

## 5. Known blockers and open issues

- Real hardware paths (camera, microphone, TTS, face recognition, object detection) are **unverified**.
- Gemini integration is unverified against the live API (no key).
- 27 identities in the local DB have no face embeddings (lost to the pre-fix shared-index defect); they need re-enrolment or deletion. Not changed automatically.
- Licensing: no repository LICENSE; AGPL-3.0 (Ultralytics) and a tracked InsightFace model need review before any commercial use. See `docs/LICENSING_REVIEW.md`.
- Many legacy documents (README badges, `docs/certification/*`) claim certification/production readiness that is not supported by evidence. See section 6.

## 6. Documentation status index

| Document | Status |
| :--- | :--- |
| `PROJECT_STATE.md`, `SYSTEM_ARCHITECTURE.md`, `CAPABILITY_VERIFICATION_MATRIX.md`, `MASTER_ROADMAP.md`, `docs/LICENSING_REVIEW.md` | **Current** (this work) |
| `README.md` | Current (rewritten in this work) |
| `docs/certification/*` (RC1 certification, safety certification, production readiness, final engineering review) | **Historical / unsupported.** Written before this audit; claims (e.g. "479 passing", "ARCHITECTURE CERTIFIED", safety certification) were not reproducible: the suite could not run from a clean clone, the scenario validator never compared results, and safety behaviour was defective. Do not cite. |
| `docs/clinical/clinical_evaluation_report.md` | Synthetic demo output (now labelled). Not clinical evidence. |
| `deployment/deployment_guide.md`, `docs/DEPLOYMENT_GUIDE.md`, `docs/OPERATIONS_MANUAL.md` | Historical; not re-verified. Use README quick start. |
| `docs/ARCHITECTURE_GUIDE.md`, `docs/architecture*`, `docs/system_architecture.md` | Historical design intent; `SYSTEM_ARCHITECTURE.md` describes code as it runs today |
| `RELEASE_NOTES.md`, `CHANGELOG.md` | Historical |

## 7. Most recent verified milestone

Core text-based product loop (talk → remember → recall after restart → inspect /
correct / export / delete) works end to end with honest safety behaviour, on
macOS and in a Linux container, from a clean install.
