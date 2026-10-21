# Release Gates and Readiness — Assessment

_2026-10-21, branch `fix/p0-data-isolation-and-safety`. Final product code: **`7c96988`**.
Clean-environment and Docker validation ran on `5c4fdf6`. `7c96988` differs from it only by
the `/delete-all` export notice and its test. It was re-checked with the dev suite, journeys
and a Docker build, and GitHub Actions re-ran the clean 3.11/3.12/3.13 and Docker jobs on the
final commit (recorded in the PR #1 description). Later commits are documentation only. A PASS
is engineering evidence only: not clinical, regulatory or commercial clearance, and not
authorisation to release._

Statuses: **PASS** (current reproducible evidence) · **FAIL** (a known defect remains) ·
**BLOCKED** (needs an owner decision or outside party) · **NOT VERIFIED** (no evidence).

## 1. Engineering checks
| Check | Status | Evidence |
| :--- | :--- | :--- |
| Full suite, dev environment (macOS arm64, Python 3.11, optional extras installed) | **PASS** | `7c96988`: 868 passed, 0 skipped, no warnings with `-W default` |
| Fresh clone + clean 3.11 venv, core + dev only | **PASS** | `5c4fdf6`: 863 passed, 4 skipped; no restricted package installed; `cv2.FaceDetectorYN` / `FaceRecognizerSF` present |
| Clean `python:3.12-slim` / `python:3.13-slim` containers | **PASS** | `5c4fdf6`: 861 passed, 6 skipped each; OpenCV 5.0.0 with YuNet/SFace classes |
| Skips, reviewed one by one | **PASS** | SpeechRecognition absent (1), google-genai absent (2): optional extras, covered in the dev environment; root ignores directory permissions in containers (2): covered in venv runs; no local DB to copy (1): covered in dev. None hides core behaviour |
| Lint (`ruff check .`) | **PASS** | clean everywhere |
| Simulated journeys | **PASS** | 20/20 everywhere |
| End-to-end text product through the CLI | **PASS** | `tests/test_cli_end_to_end.py` |
| Consent at application and storage layers (incl. no face embedding without consent) | **PASS** | `test_consent_policy.py`, `test_consent_enforcement.py`, `test_face_recognition_sface.py` |
| Delete-all and export after identity learning | **PASS** | `test_delete_all_after_identity_learning_…`, `test_export_contains_every_stored_personal_row`, `test_delete_all_tells_the_person_that_their_export_file_still_exists` |
| Face recognition logic (YuNet + SFace) with synthetic stand-ins | **PASS** | 15 tests; mutation-checked consent and ambiguity tests |
| Face recognition with real model files | **NOT VERIFIED** | models not downloaded (D3; download approval) |
| Real camera / microphone / speaker | **NOT VERIFIED** | not run, by instruction |
| Voice path offline (buffers, model failure, availability) | **PASS** | `test_voice_path_offline.py` |
| Network policy; dashboard offline | **PASS** | `test_network_policy.py`, `test_dashboard_loads_nothing_from_the_internet` |
| Hardware only via `--live-hardware`; no fabricated faces | **PASS** | `test_hardware_activation_is_explicit.py`, `test_no_physical_devices.py` |
| Simulation/test isolation; read-only diagnostics | **PASS** | `test_simulation_isolation.py`, `test_check_never_modifies_or_creates_the_user_database` |
| Backup/restore/corruption; manifest validation | **PASS** | `test_backup_restore.py`, CLI journey |
| Docker build, diagnostics, persistence, contents | **PASS** | `5c4fdf6` and `7c96988` images: `--check` passes; memory, locations and export persist on a disposable volume; delete-all works; uid 10001; files 0600; headless OpenCV; **no `.onnx` file, no `assets/`, no restricted package**; `/app/licenses` notices + SBOM |
| Secret scan, full history | **PASS** | 134 commits (re-run before the final commit): no key/token/private-key patterns; no database, log, embedding or backup file ever committed; the only model ever tracked is the InsightFace SCRFD file (D1) |
| Owner data | **FAIL (incident, contained)** | F-04: live DB migrated on 2026-10-21 06:01; rows unchanged; pre-incident copy byte-identical and secured; restoration awaits the owner (`docs/DATABASE_INCIDENT_RECORD.md`). Unchanged during this mission: live `972ed943…`, pre-incident `26f38093…`, 29 Sep backup `d8d8ccd7…` (SHA-1) |
| macOS PyAV/OpenCV `libavdevice` (R-09) | **NOT VERIFIED** | known upstream risk; text mode never loads PyAV; the image has no `libavdevice` |
| Windows | **NOT VERIFIED** | — |

## 2. Gates
| Gate | Status | Basis | What remains |
| :--- | :--- | :--- | :--- |
| A. Clean installation | **PASS** (macOS, Linux; 3.11–3.13) | §1 | Windows NOT VERIFIED |
| B. Core user journey (text) | **PASS** | journeys, CLI end-to-end, Docker | — |
| C. Data integrity | **PASS** for the software; owner-DB incident recorded | §1 | Owner decision on restoring the migrated local DB (`docs/DATABASE_INCIDENT_RECORD.md`) |
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
| D. Real-hardware operation | **Not ready** | Devices off unless `--live-hardware`; no fabricated faces; YuNet + SFace backend implemented and tested with stand-ins | Every device path; real model files; R-09 | D3 (models), D1/D2; authorised hardware session (`docs/HARDWARE_TEST_CHECKLIST.md`) |
| E. Use by people with memory difficulties | **Not ready** | Software safeguards only | Clinical safety, usability with the intended population and carers | Clinical and ethics review; supervised studies; regulatory assessment (medical-device status) |
| F. Commercial distribution | **Not ready; BLOCKED** | Core build has no non-commercial/AGPL component | Legal review | Repository licence and contributor/competition rights; InsightFace model; AGPL; Gemini terms; notices; regulatory and privacy compliance |

Passing software tests does not establish clinical safety, regulatory compliance, suitability
for unsupervised use, or commercial rights.

## 5. Owner decisions and external reviews (prioritised)
| # | Decision | Options | Recommendation |
| :--- | :--- | :--- | :--- |
| 1 | Local database after the incident | A keep migrated · B restore exact pre-incident copy (procedure in `docs/DATABASE_INCIDENT_RECORD.md`) · C either, plus a fresh DB for real use | B for an exact archive, else A; C for real use |
| 2 | Repository licence and rights (D6) | Identify the competition programme and its IP terms; get all four contributors' written agreement; then choose (options in `docs/LICENSING_REVIEW.md` §5) | Start with the programme rules |
| 3 | Tracked InsightFace model (D1) | Stop tracking it in a new commit (stays in history) · licence it · keep | Stop tracking it |
| 4 | Face-recognition models (D3) | Approve downloading the opencv_zoo YuNet/SFace files for **local evaluation** after counsel's view on training-data terms · obtain a commercially cleared model · keep face recognition off | Keep off for any pilot; approve local evaluation only for an authorised hardware test |
| 5 | Hardware test session | Authorise `docs/HARDWARE_TEST_CHECKLIST.md` on a named machine with consenting adults · not now | — |
| 6 | Supervised text-only pilot | Authorise per `docs/PILOT_CHECKLIST.md` (needs 2, privacy notice, ethics decision, safety person) · not now | — |
| 7 | Banner image (D4), YOLO (D2), Gemini (D5) | Remove/record banner · keep YOLO optional, never distributed · keep Gemini off | As stated |
| 8 | Merge PR #1 | after review | — |

External reviews still required: legal (licences, contributor rights, competition terms,
training-data terms, Gemini terms); biometric-privacy and data-protection review; clinical
review of urgent-phrase handling and wording; usability with people with memory difficulties
and carers; regulatory assessment (medical-device status).

## 4. Reproduction (from a clean checkout)
```bash
python3.11 -m venv .venv-check && .venv-check/bin/pip install -r requirements-dev.txt
export MEMORA_DB_PATH=$(mktemp -d)/memora.sqlite MEMORA_LOG_DIR=$(mktemp -d)
.venv-check/bin/ruff check .
.venv-check/bin/python -m pytest tests/ -q -p no:cacheprovider -rs
.venv-check/bin/python app.py --simulate
.venv-check/bin/python app.py --check
python deployment/provision_face_models.py --status        # models are optional; expect "not provisioned"
git archive HEAD | docker run --rm -i python:3.13-slim sh -c "apt-get update -qq && apt-get install -y -qq libgl1 libglib2.0-0 >/dev/null; mkdir /s && cd /s && tar xf - && pip install -q -r requirements-dev.txt && python -m pytest tests/ -q -p no:cacheprovider -rs"
docker build -t memora -f deployment/docker/Dockerfile . && docker run --rm memora python app.py --check
```
Always set `MEMORA_DB_PATH` and `MEMORA_LOG_DIR` first; without them commands use the
project-folder database.
