# Release Gates and Readiness — Assessment

_2026-10-21, branch `fix/p0-data-isolation-and-safety`. Product code validated at commit
**`2990621`**. Later commits change only documentation and test hygiene (closing unclosed
files in tests), with no product code (`git diff --stat 2990621..HEAD -- . ':!*.md' ':!tests/'`
is empty). The suite and GitHub Actions were re-run on the final commit; the PR description
records that CI run. A PASS is engineering evidence only: it is not clinical, regulatory or
commercial clearance, and it does not authorise a release._

Statuses: **PASS** (current reproducible evidence) · **FAIL** (a known defect remains) ·
**BLOCKED** (needs an owner decision or outside party) · **NOT VERIFIED** (no evidence).

## 1. Engineering checks
| Check | Status | Evidence |
| :--- | :--- | :--- |
| Full suite, dev environment (macOS arm64, Python 3.11, all optional extras) | **PASS** | 840 passed, 0 skipped. With `-W default`: 0 warnings apart from two third-party `DeprecationWarning`s from `speech_recognition` (imports `aifc`/`audioop`; optional hardware package) |
| Fresh clone + clean 3.11 venv, core + dev only | **PASS** | 836 passed, 4 skipped; none of insightface, ultralytics, faster-whisper, google-genai, mediapipe, SpeechRecognition or av installed |
| Clean `python:3.12-slim` / `python:3.13-slim` containers (`git archive`) | **PASS** | 834 passed, 6 skipped each |
| Skips, reviewed one by one | **PASS** | SpeechRecognition absent (1) and google-genai absent (2): optional extras, covered in the dev environment; root ignores directory permissions in containers (2): covered in the venv runs; no local database to copy in a clean checkout (1): covered in the dev environment. No skip hides core behaviour |
| Lint (`ruff check .`, correctness rules) | **PASS** | clean in every environment |
| Simulated journeys (`app.py --simulate`) | **PASS** | 20/20 in all environments |
| End-to-end text product through the CLI | **PASS** | `tests/test_cli_end_to_end.py` (consent → correction → restart → backup → damaged DB → `--check` → restore → delete-all → restart) |
| Consent at application and storage layers | **PASS** | `test_consent_policy.py` (persisted state, marker absent from every file, identity evidence, export completeness), `test_consent_enforcement.py`, journey `consent_declined` |
| Network policy | **PASS** | `test_network_policy.py` (socket interception); `test_dashboard_loads_nothing_from_the_internet`; `--check` "Network Use: Nothing" |
| Hardware only via `--live-hardware`; no fabricated faces | **PASS** | `test_hardware_activation_is_explicit.py` (26 cases), `test_no_physical_devices.py` |
| Simulation and test isolation | **PASS** | `test_simulation_isolation.py`; `memora-tests-*` count unchanged across full runs |
| Diagnostics read-only | **PASS** | `test_check_never_modifies_or_creates_the_user_database` |
| Backup / restore / corruption recovery / manifest validation | **PASS** | `test_backup_restore.py`, CLI journey |
| Identity conflicts and false-memory prevention | **PASS** | `test_identity_learning_pipeline.py`, `test_conversational_memory.py` (corrections, place-not-name, locations) |
| Docker build, diagnostics, persistence | **PASS** | built from `2990621`; `--check` passes (warning only for absent optional packages); memory and locations persist across runs on a volume; uid 10001; DB and export 0600; no `assets/`, no restricted packages, PyAV not loaded |
| Secret scan, full history (126 commits) | **PASS** | no key/token/private-key patterns; no database, embedding, log or backup file ever committed |
| GitHub Actions | **PASS** on `e5c582b` (8/8 jobs); final commit: see PR #1 description | core on 3.11/3.12/3.13 + docker |
| Clean development database procedure | **PASS** | `deployment/create_dev_database.py`, `test_create_dev_database.py`, demonstrated in a temporary folder |
| Owner data preserved | **FAIL (incident, contained)** | Owner backup (`d8d8ccd7…`) and untracked files unchanged. The owner database was **migrated by an engineering `--check` run** (ledger F-04): all existing rows unchanged (row-by-row comparison), changes additive only, byte-identical pre-incident copy secured. The cause is fixed and tested. Restoring the live file is the owner's decision |
| Windows | **NOT VERIFIED** | no Windows environment used |
| macOS hardware install: PyAV/OpenCV duplicate `libavdevice` (R-09) | **NOT VERIFIED** | known upstream risk, not reproduced; text mode never loads PyAV; manual procedure in `docs/HARDWARE_TEST_CHECKLIST.md` |
| Camera, microphone, ASR, TTS on real devices | **NOT VERIFIED** | not run, by instruction |
| Real face recognition | **FAIL** | no working backend with the pinned hardware packages (ledger F-07); fabrication prevented; needs decision D3 |

## 2. Gates
| Gate | Status | Basis | What remains |
| :--- | :--- | :--- | :--- |
| A. Clean installation | **PASS** (macOS, Linux; 3.11–3.13) | §1 | Windows NOT VERIFIED |
| B. Core user journey (text) | **PASS** | journeys, CLI end-to-end, Docker | — |
| C. Data integrity | **PASS** for the software; owner-DB incident recorded | §1 | Owner decision on the migrated local DB (C2-24, F-04) |
| D. Safety behaviour (software) | **PASS** | urgent detection incl. lead words, delivery-path guard, honest action boundaries | Clinical review of wording: **BLOCKED** (clinicians) |
| E. Simulation honesty and isolation | **PASS** | §1 | — |
| F. Security and privacy (software scope) | **PASS** | consent at both layers, network policy, read-only diagnostics, 0600 files, delete-all, complete export, dashboard hardening, manifest validation, secret scan | Not implemented: encryption at rest, secure erase, per-person consent. Gemini terms: **BLOCKED** (D5) |
| G. Stability | **PASS (simulated, ≤ 20 min)** | soaks in `docs/evidence/`; repeated start/stop | Multi-hour and hardware runs NOT VERIFIED |
| H. Deployment | **PASS (core)** | Docker image, healthcheck, `/data` volume, CI | Image not published (needs authorisation; build with `opencv-python-headless` first, `docs/LICENSING_REVIEW.md`) |
| I. Documentation | **PASS** | README, PROJECT_STATE, architecture, capability matrix, roadmap, safety, privacy, licensing, ledger, checklists checked against the code | — |
| J. External readiness | **BLOCKED** | — | Licence and asset decisions D1–D7; clinical, usability, privacy and regulatory review; hardware validation |

## 3. Readiness by use
| Use | Verdict | Verified | Not verified | Blocks progression |
| :--- | :--- | :--- | :--- | :--- |
| A. Local text-only development | **Ready** | Everything in §1 for the text product; clean dev database tool | Windows | — |
| B. Reproducible text-only install and Docker | **Ready (engineering)**; not published | clean installs 3.11–3.13; Docker build, persistence, non-root | Windows; image signing/SBOM | Authorisation to publish; LGPL notices for bundled OpenCV libraries; repository licence |
| C. Controlled, supervised technical pilot (text only) | **Engineering-ready; not authorised** | as A/B, plus honest boundaries and data controls | Real users' phrasing; usability | Owner approval, licence or pilot agreement (D6), privacy notice, ethics decision, named safety person (`docs/PILOT_CHECKLIST.md`) |
| D. Real-hardware operation | **Not ready** | Devices off unless `--live-hardware`; no fabricated faces | Every device path; R-09 | No working face-recognition backend (D3); licence decisions D1/D2; authorised hardware session (`docs/HARDWARE_TEST_CHECKLIST.md`) |
| E. Use by people with memory difficulties | **Not ready** | Software safeguards only | Clinical safety, usability with the intended population and carers | Clinical and ethics review; supervised studies; regulatory assessment (medical-device status) |
| F. Commercial distribution | **Not ready; BLOCKED** | Core build has no non-commercial/AGPL component | Legal review | Repository licence and contributor/competition rights; InsightFace model; AGPL; Gemini terms; notices; regulatory and privacy compliance |

Passing software tests does not establish clinical safety, regulatory compliance, suitability
for unsupervised use, or commercial rights.

## 4. Reproduction (from a clean checkout)
```bash
python3.11 -m venv .venv-check && .venv-check/bin/pip install -r requirements-dev.txt
export MEMORA_DB_PATH=$(mktemp -d)/memora.sqlite MEMORA_LOG_DIR=$(mktemp -d)
.venv-check/bin/ruff check .
.venv-check/bin/python -m pytest tests/ -q -p no:cacheprovider -rs
.venv-check/bin/python app.py --simulate
.venv-check/bin/python app.py --check
git archive HEAD | docker run --rm -i python:3.13-slim sh -c "apt-get update -qq && apt-get install -y -qq libgl1 libglib2.0-0 >/dev/null; mkdir /s && cd /s && tar xf - && pip install -q -r requirements-dev.txt && python -m pytest tests/ -q -p no:cacheprovider -rs"
docker build -t memora -f deployment/docker/Dockerfile . && docker run --rm memora python app.py --check
```
Always set `MEMORA_DB_PATH` and `MEMORA_LOG_DIR` first; without them commands use the
project-folder database.
