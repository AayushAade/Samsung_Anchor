# Hardware Test Checklist (not yet executed)

_Prepared 2026-10-21. No step below has been run: real devices were not used in engineering
work, by instruction. Run this only with the owner's explicit authorisation, on a named
machine, with consenting adults, and with synthetic or consented data._

## 0. Preconditions
- [ ] Owner authorisation recorded (who, which machine, date).
- [ ] Separate data location, never the project-folder database:
      `export MEMORA_DB_PATH=~/memora-data/hwtest/memora.sqlite MEMORA_LOG_DIR=~/memora-data/hwtest/logs`
- [ ] `pip install -r requirements-hardware.txt` in a dedicated virtual environment; record
      `pip freeze` in the test log.
- [ ] Licence decisions taken for any model that will be loaded (`docs/LICENSING_REVIEW.md`):
      InsightFace models (non-commercial), YOLO (AGPL). If not decided, do not load them.
- [ ] Network: leave every `MEMORA_ALLOW_*` unset unless that specific item is under test.
      If the speech model is not on disk, download it once with
      `MEMORA_ALLOW_MODEL_DOWNLOAD=1` and record its source and checksum.
- [ ] `python app.py --check` (with the variables above): record every WARN line.

## 1. Device activation is explicit
- [ ] `python app.py --chat`: macOS shows **no** camera or microphone indicator.
- [ ] `python app.py --simulation --max-cycles 5`: no device indicator.
- [ ] `MEMORA_PROFILE=LAPTOP python app.py --max-cycles 5`: no device indicator (profile alone must not enable devices).
- [ ] `python app.py --vision-standalone`: exits with code 2 and opens nothing.
- [ ] `python app.py --live-hardware --max-cycles 20`: camera indicator on during the run and
      off afterwards; microphone only after `/consent voice on` in a prior chat session.

## 2. Consent with real sensors
- [ ] Without `/consent faces on`: a face in view is not enrolled (`python app.py --show-memory` shows no new people).
- [ ] With faces and memory consent: one enrolment; `--show-memory` lists it; `/delete-all` in chat removes it and its face files.
- [ ] Without `/consent voice on`: identity learning does not open the microphone.
- [ ] With `MEMORA_ALLOW_CLOUD_ASR` unset: no connection to Google speech services (check with
      a network monitor such as Little Snitch, or `nettop -p <pid>`).

## 3. Audio and speech
- [ ] Speech output is audible and is not spoken twice.
- [ ] Recorded speech is transcribed locally; the transcript is shown only in the debug log when memory consent is on.
- [ ] Urgent phrases spoken aloud ("I fell", "I can't breathe") produce urgent guidance.

## R-09. PyAV / OpenCV duplicate `libavdevice` (macOS)
**What is known.** `av` 18.0.0 bundles `libavdevice.62.3.102.dylib` and `opencv-python`
5.0.0.93 bundles `libavdevice.61.3.100.dylib`. Both define the Objective-C classes
`AVFFrameReceiver` and `AVFAudioReceiver`, so loading both in one process prints a
duplicate-class warning. Upstream PyAV issue #2215 was closed "not planned". One other project
(pollen-robotics/reachy-mini-desktop-app #176) suspected it of causing a SIGTRAP crash, but its
maintainer later attributed that crash to code signing and bundling, and another user saw only
the warning. No crash confirmed to come from this conflict has been found (sources read
2026-10-21).
`opencv-python-headless` 5.0.0.93 bundles the same `libavdevice.61.3.100.dylib`, so switching
to it does not remove the conflict (wheel contents inspected 2026-10-21).

**What MEMORA does.** Text chat, simulation and `--check` never import PyAV
(`tests/test_media_library_isolation.py`). In voice mode faster-whisper imports PyAV; MEMORA
passes audio as NumPy arrays (PyAV's decoder is not called) and opens the camera through
OpenCV's native AVFoundation backend first. By code reading, the duplicated classes (FFmpeg's
AVFoundation capture device) are not used, but this is an inference, not a test result.

**What is unknown.** Whether a live session with camera and voice on the same process is
stable on macOS.

**Manual validation procedure.**
- [ ] `python app.py --check` shows the "Media Libraries" warning (confirms both copies are present).
- [ ] Run `python app.py --live-hardware` with camera and voice for 30 minutes, with at least
      20 spoken turns and repeated face entry/exit. Record any `objc` messages, crashes (exit
      code, `~/Library/Logs/DiagnosticReports/Python*.ips`) and freezes.
- [ ] Repeat once after `pip install "av==<version whose libavdevice matches cv2>"` if such a
      version exists (matching versions still warn, but may behave identically).
- [ ] If any crash occurs: record it in `docs/EXECUTION_LEDGER.md` (R-09) and move speech
      recognition into a separate process. That is a design change and needs owner approval.

## 4. Stability
- [ ] 2-hour live run; record memory use (Activity Monitor) at start, 1 h and 2 h; no growth trend.
- [ ] Unplug or disable the camera during a run: MEMORA reports it and keeps running.

## 5. Record keeping
- [ ] Results, logs (with personal content removed), versions and dates in `docs/evidence/`.
- [ ] Update `CAPABILITY_VERIFICATION_MATRIX.md` statuses only for what was actually observed.
