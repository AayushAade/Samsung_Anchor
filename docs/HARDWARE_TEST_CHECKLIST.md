# Hardware Test Checklist (not yet executed)

_Updated 2026-10-21. No step below has been run: no camera, microphone or speaker was used
in engineering work, by instruction. Run this only with the owner's explicit, written
authorisation, on a named machine, with consenting adults, using a separate test database.
Text-mode behaviour is covered by automated tests; this checklist covers only what needs
real devices._

## 0. Prerequisites
| # | Item | Command / action | Expected |
| :--- | :--- | :--- | :--- |
| 0.1 | Authorisation recorded | who, which machine, date, which sections | written approval |
| 0.2 | Licence decisions for any model to be loaded | `docs/LICENSING_REVIEW.md` D1–D3 | decided; otherwise skip §2 |
| 0.3 | Dedicated environment | `python3.11 -m venv .venv-hw && .venv-hw/bin/pip install -r requirements-hardware.txt` | installs; save `pip freeze > hw-freeze.txt` |
| 0.4 | Separate data folder (never the project-folder DB) | `python deployment/create_dev_database.py ~/memora-data/hwtest` then `export MEMORA_DB_PATH=~/memora-data/hwtest/memora.sqlite MEMORA_LOG_DIR=~/memora-data/hwtest/logs` | "Created and verified … 0 personal rows" |
| 0.5 | Network stays off | leave all `MEMORA_ALLOW_*` unset | — |
| 0.6 | Face models (only if 0.2 allows) | download the files yourself from opencv_zoo, then `python deployment/provision_face_models.py --from <folder>` | "Installed and verified …" for a detector and `face_recognition_sface_2021dec.onnx` |
| 0.7 | Speech model (optional) | if not on disk, run once with `MEMORA_ALLOW_MODEL_DOWNLOAD=1`; record source and checksum | model in the Hugging Face cache |
| 0.8 | Diagnostics | `python app.py --check` | Network Use: PASS "Nothing"; Face Recognition Models: PASS (if 0.6); Media Libraries: WARN on macOS (R-09) |
| 0.9 | Baseline checksum of the test DB | `shasum -a 256 ~/memora-data/hwtest/memora_v2.sqlite` | recorded |

## 1. Device activation is explicit
| # | Command | Expected |
| :--- | :--- | :--- |
| 1.1 | `python app.py --chat`, type `/quit` | no camera or microphone indicator |
| 1.2 | `python app.py --simulation --max-cycles 5` | no device indicator |
| 1.3 | `MEMORA_PROFILE=LAPTOP python app.py --max-cycles 5` | no device indicator (a profile alone never enables devices) |
| 1.4 | `python app.py --vision-standalone` | exits with code 2; opens nothing |
| 1.5 | `python app.py --live-hardware --max-cycles 20` | camera indicator on during the run, off afterwards; the status table lists Camera, Audio, Speech Recognition, Face Recognition with honest states |

## 2. Face recognition (only after D3 and with consenting adults)
| # | Step | Expected |
| :--- | :--- | :--- |
| 2.1 | Without `/consent faces on`, a person in view for 30 s | label "Face recognition is off (no consent)"; `python app.py --show-memory` shows no new people |
| 2.2 | `/consent memory on` and `/consent faces on` in chat; one person in view ≥ 15 stable frames | exactly one anonymous person enrolled |
| 2.3 | Same person leaves and returns | recognised as the same id; no new person |
| 2.4 | A second consenting person | a different id; never named as the first |
| 2.5 | Two people who look alike (if available) | "Not sure who this is" rather than a wrong name |
| 2.6 | Poor light / far away | ignored or "Detecting…", never a wrong name |
| 2.7 | `/consent faces off` | matching stops at once; reply states stored face data is kept |
| 2.8 | `/delete-all` | `--show-memory` shows no people; face files emptied |
| 2.9 | Record false-match and missed-match counts | input for calibrating `SFACE_MATCH_TOLERANCE` (currently 1.0, uncalibrated) |

## 3. Microphone, speech and speaker
| # | Step | Expected |
| :--- | :--- | :--- |
| 3.1 | `--live-hardware` without `/consent voice on` | identity learning does not open the microphone |
| 3.2 | With voice consent, `MEMORA_ALLOW_CLOUD_ASR` unset | no connection to Google (`nettop -p <pid>` or a firewall log); typing fallback only in a terminal |
| 3.3 | Status table with speech model absent | at start-up "Speech Recognition: WARNING (… loads on first use (must already be on this computer) …)"; after the first speech attempt "FAILED (… not available locally …)" |
| 3.4 | With local model present, speak 10 sentences | transcripts appear in the debug log only when memory consent is on |
| 3.5 | Spoken urgent phrases ("I fell", "I can't breathe") | urgent guidance |
| 3.6 | Speaker output | audible once (no double speech); with no audio backend the status says so |

## R-09. PyAV / OpenCV duplicate `libavdevice` (macOS)
**Known.** `av` 18.0.0 bundles `libavdevice.62.3.102.dylib` and `opencv-python` 5.0.0.93
bundles `libavdevice.61.3.100.dylib`; both define `AVFFrameReceiver` and `AVFAudioReceiver`.
Loading both prints a duplicate-class warning. PyAV issue #2215 was closed "not planned". One
other project's crash was suspected and later attributed by its maintainer to code signing.
`opencv-python-headless` bundles the same `libavdevice` on macOS (wheel inspected), so it does
not help there. On Linux, the headless wheel (used in the Docker image) bundles no
`libavdevice`.

**MEMORA.** Text chat, simulation and `--check` never import PyAV
(`tests/test_media_library_isolation.py`). Voice mode imports PyAV through faster-whisper.
MEMORA passes audio as arrays (PyAV's decoder is not called) and opens the camera through
OpenCV's AVFoundation backend first. By code reading, the duplicated classes are unused; this
is an inference, not a result.

**Procedure.**
- [ ] 0.8 shows the Media Libraries warning.
- [ ] 30-minute `--live-hardware` run with camera and voice, ≥ 20 spoken turns, repeated face
      entry/exit. Record `objc` messages, crashes (`~/Library/Logs/DiagnosticReports/Python*.ips`)
      and freezes.
- [ ] If a crash occurs: record it in `docs/EXECUTION_LEDGER.md` (R-09). Next step (needs owner
      approval): run speech recognition in a separate process.

## 4. Stability
- [ ] 2-hour `--live-hardware` run; memory use at 0, 60 and 120 minutes; no growth trend.
- [ ] Disconnect the camera mid-run: status shows FAILED; MEMORA keeps running.

## 5. Cleanup and rollback
- [ ] `/delete-all` in chat (test data), then remove `~/memora-data/hwtest` yourself if no longer needed.
- [ ] Remove face models if the trial ends: delete `data/models/face/` (or `MEMORA_FACE_MODEL_DIR`).
- [ ] Remove the environment: delete `.venv-hw`.
- [ ] Revoke macOS camera/microphone permission for Terminal/Python if granted only for the test
      (System Settings → Privacy & Security).
- [ ] Rollback: nothing in the project folder or the owner's database is touched when 0.4 is
      followed. Confirm the owner DB checksum is unchanged:
      `shasum -a 256 memora_db_v2.sqlite` (expected value in `docs/DATABASE_INCIDENT_RECORD.md`).

## 6. Recording results
- [ ] Versions (`hw-freeze.txt`), dates, machine, results and logs (personal content removed) in `docs/evidence/`.
- [ ] Update `CAPABILITY_VERIFICATION_MATRIX.md` only for what was actually observed.
