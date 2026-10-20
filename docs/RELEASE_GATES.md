# Release Gates — Assessment

_2026-10-21, branch `fix/p0-data-isolation-and-safety`. Validated **code commit `09cf8ac`**;
later commits change only documentation and add test cases. They change no product code, as
`git diff --stat 09cf8ac..HEAD` shows (only `.md` files and `tests/`), and the suite and CI were
re-run on the final commit. PASS means the evidence below was produced on that commit and can be
reproduced with the commands at the end. It does **not** mean clinical, regulatory or
commercial readiness, and it does not authorise a release._

Verdicts: **PASS** (evidence produced) · **FAIL** (a check ran and did not meet the bar) ·
**BLOCKED** (needs a decision or resource outside engineering) · **NOT VERIFIED** (not run).

## Engineering checks on `09cf8ac`
| Check | Verdict | Evidence |
| :--- | :--- | :--- |
| Test suite (dev environment, macOS, Python 3.11) | **PASS** | 812 passed, 0 skipped; 815 passed on the final commit, which adds three cases checking that urgent statements with a leading "Actually"/"No,"/"Well," still get urgent guidance |
| Fresh clone + clean venv, core + dev deps only (macOS, 3.11) | **PASS** | 808 passed, 4 skipped; none of insightface, ultralytics, faster-whisper, google-genai, mediapipe, SpeechRecognition installed |
| Clean `python:3.12-slim` container (`git archive`, core + dev) | **PASS** | 806 passed, 6 skipped |
| Clean `python:3.13-slim` container (`git archive`, core + dev) | **PASS** | 806 passed, 6 skipped |
| Skips reviewed individually | **PASS** | SpeechRecognition / google-genai absent (optional extras, 3 tests); root ignores directory permissions in containers (2 tests); no local database to copy in clean checkouts (1 test). No skip hides a core behaviour |
| Simulated journeys (`app.py --simulate`) | **PASS** | 20/20 in all four environments |
| End-to-end text product via the real CLI | **PASS** | `tests/test_cli_end_to_end.py`: consent → conversation → spoken correction → restart → backup → damaged DB (`--check` exit 1, chat exit 2 with guidance) → restore → delete-all → restart; logs free of names |
| Lint (ruff correctness rules) | **PASS** | "All checks passed" in every environment |
| Consent policy across writes, commands, doses, logs | **PASS** | `test_consent_policy.py`, `test_consent_enforcement.py`, `consent_declined` journey |
| Network policy (socket interception) | **PASS** | `test_network_policy.py`; `--check` "Network Use: Nothing" locally and in Docker |
| Hardware only via `--live-hardware` | **PASS** | `test_hardware_activation_is_explicit.py` (23 cases incl. `--vision-standalone`); suite-wide device guard `test_no_physical_devices.py` |
| Simulation isolation | **PASS** | `test_simulation_isolation.py`; real environment: 65 entries unchanged after `--simulate` |
| Backup / restore | **PASS** | `test_backup_restore.py` (round trip, tamper, corrupt live DB, manifest path traversal) + CLI journey |
| Docker build, diagnostics, persistence | **PASS** | image built; `--check` passes (only warning: optional packages absent); chat persists across container runs on a volume; runs as uid 10001; DB file 0600 |
| Secret scan, full history (116 commits) | **PASS** | no key/token/private-key patterns; only placeholders `your-gemini-api-key`; no database, embedding or backup files ever committed |
| GitHub Actions on `09cf8ac` | **PASS** | push and pull_request runs green: core on 3.11, 3.12, 3.13 + docker job |
| Owner data unchanged | **PASS** | `memora_db_v2.sqlite` SHA-1 `26f38093…` and `~/memora_backups/20261020/` SHA-1 `d8d8ccd7…` unchanged; 16 untracked owner files untouched |
| Windows | **NOT VERIFIED** | no Windows environment used |
| Voice mode, camera, real speaker | **NOT VERIFIED** | real devices were not used during this mission, by instruction |
| Hardware install on macOS (PyAV + OpenCV duplicate `libavdevice`, ledger R-09) | **NOT VERIFIED** | warning observed; no crash reproduced |

## Gates
| Gate | Verdict | Basis | What remains |
| :--- | :--- | :--- | :--- |
| **A. Clean installation** | **PASS** (macOS, Linux containers; 3.11–3.13) | rows above | Windows NOT VERIFIED |
| **B. Core user journey** | **PASS (text mode)** | journeys + CLI end-to-end + Docker persistence | Voice mode NOT VERIFIED |
| **C. Data integrity** | **PASS** | isolation, backup/restore, migrations, owner data unchanged | Local DB contamination: owner decision (C2-24) |
| **D. Safety behaviour** | **PASS (software)** | urgent detection, delivery-path guard, boundaries, journeys | Clinical review of wording — BLOCKED (needs clinicians) |
| **E. Simulation honesty & isolation** | **PASS** | labelled sources; isolated workspace; explicit hardware activation | — |
| **F. Security & privacy** | **PASS (software scope)** | consent policy, network policy, 0600 files, delete-all, dashboard hardening, path validation, secret scan | Not implemented: encryption at rest, secure erase, per-person consent. Gemini API terms review — BLOCKED (legal) |
| **G. Stability** | **PASS (simulated, ≤ 20 min)** | soaks in `docs/evidence/`; repeated start/stop leaves no threads or file descriptors | Multi-hour and real-hardware runs NOT VERIFIED |
| **H. Deployment** | **PASS (core)** | Docker image, healthcheck, `/data` volume, CI | Hardware extras not packaged; no image published (requires authorisation) |
| **I. Documentation** | **PASS** | README checked against the CLI; PROJECT_STATE, architecture, capability matrix, roadmap, safety, privacy, licensing, ledger updated | — |
| **J. External readiness** | **BLOCKED** | — | Repository licence; InsightFace model (tracked in public repo) and AGPL decisions; banner provenance; clinical/usability evaluation; privacy/regulatory review; hardware validation |

## Conclusion
Software engineering for the **text product** has met every gate it can meet without outside
parties. It is suitable for a **supervised technical pilot** using the core install or Docker
image, with consenting participants, a named person responsible for safety, and non-critical
data. It is **not** authorised or ready for unsupervised use by people with memory difficulties,
real-hardware deployment, or commercial distribution. Gate J needs the owner, contributors,
counsel and clinicians. **Release authorisation is the owner's decision, not an engineering
result.**

## Reproduction (from a clean checkout of the validated commit)
```bash
python3.11 -m venv .venv-check && .venv-check/bin/pip install -r requirements-dev.txt
export MEMORA_DB_PATH=$(mktemp -d)/memora.sqlite MEMORA_LOG_DIR=$(mktemp -d)
.venv-check/bin/ruff check .
.venv-check/bin/python -m pytest tests/ -q -p no:cacheprovider -rs
.venv-check/bin/python app.py --simulate
.venv-check/bin/python app.py --check
git archive 09cf8ac | docker run --rm -i python:3.13-slim sh -c "apt-get update -qq && apt-get install -y -qq libgl1 libglib2.0-0 >/dev/null; mkdir /s && cd /s && tar xf - && pip install -q -r requirements-dev.txt && python -m pytest tests/ -q -p no:cacheprovider -rs"
docker build -t memora -f deployment/docker/Dockerfile . && docker run --rm memora python app.py --check
```
