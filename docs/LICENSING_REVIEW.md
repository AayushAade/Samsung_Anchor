# Licensing and Commercial-Readiness Review (engineering notes — not legal advice)

_Updated 2026-10-21 (remediation mission); first written 2026-10-20. Sources: installed package metadata (`importlib.metadata`) and
the projects' own published terms (fetched 2026-10-20). Every item marked
**review** needs confirmation by qualified counsel before any commercial
distribution. MEMORA is **not** cleared for commercial distribution._

## 1. The repository itself
- **Public** GitHub repository (verified with `gh`, 2026-10-20). Everything committed —
  code, documents, and the tracked model file below — has been publicly disclosed.
- **No LICENSE file.** The README describes it as a Samsung Solve For Tomorrow
  competition entry. Ownership of contributions from several contributors and any
  competition terms must be clarified before choosing a licence — **review**.
- Public disclosure may affect the ability to patent any mechanism described in the
  repository; see `docs/product/PRODUCT_SPEC.md`. No filing or legal decision has been made.

## 2. Dependency inventory

### Core runtime (`requirements.txt`) — needed for text conversation, memory, diagnostics
| Package | Version | Declared licence | Commercial use | Obligations |
| :--- | :--- | :--- | :--- | :--- |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Permitted | Keep notices |
| SQLAlchemy | 2.0.51 | MIT | Permitted | Keep notice |
| faiss-cpu | 1.14.3 | MIT | Permitted | Keep notice |
| opencv-python | 5.0.0.93 | Apache-2.0 | Permitted | Notice; bundled codecs (FFmpeg, LGPL) — **review** for binary redistribution |
| psutil | 7.2.2 | BSD-3-Clause | Permitted | Notice |
| pydantic | 2.13.4 | MIT | Permitted | Notice |
| websockets | 16.0 | BSD-3-Clause | Permitted | Notice |

All core dependencies are permissive. A product built from `requirements.txt` only,
**without** `assets/models/` or `yolov8n.pt`, uses no copyleft or non-commercial
component that we have identified. (The Docker image is built this way.)

### Optional: sensors and on-device models (`requirements-hardware.txt`)
| Package / asset | Licence evidence | Commercial implication | Options |
| :--- | :--- | :--- | :--- |
| ultralytics 8.4.87 | Metadata: AGPL-3.0. Ultralytics licence page: YOLO models are AGPL-3.0 by default; closed-source/commercial use requires a paid Enterprise licence | Closed-source distribution **not permitted** without an Enterprise licence; network use triggers AGPL source obligations | Keep optional; obtain Enterprise licence, or replace with a permissively licensed detector |
| `yolov8n.pt` (local, git-ignored, not tracked) | Ultralytics weights, AGPL-3.0 per Ultralytics | As above; not downloaded unless the file already exists or `MEMORA_ALLOW_MODEL_DOWNLOAD=1` | Do not ship |
| insightface 1.0.1 (code) | README: code under MIT, "no limitation for both academic and commercial usage"; metadata declares no licence | Code permitted | — |
| InsightFace pretrained models, incl. **`assets/models/scrfd_500m_bnkps.onnx` (tracked in git)** | README: training data "and the models trained with these data are available for non-commercial research purposes only"; commercial licensing via InsightFace (contacts listed in their README) | **Non-commercial only.** The file is publicly redistributed by this repository today | Owner decision: stop tracking/redistributing it (history keeps it), obtain a commercial licence, or replace. The main recogniser does not load it (it looks in `assets/`, not `assets/models/`); `src/vision/detector.py` does |
| mediapipe 0.10.35 | Apache-2.0 | Permitted; check bundled model cards | Notice |
| faster-whisper 1.2.1 | MIT | Permitted. Weights (`Systran/faster-whisper-tiny.en`, MIT per model card) are **not downloaded** unless `MEMORA_ALLOW_MODEL_DOWNLOAD=1`; otherwise only a pre-installed local copy is used (`local_files_only`) | Notice; record provenance of any bundled weights |
| onnxruntime 1.27.0 | MIT | Permitted | Notice |
| PyAudio 0.2.14 | MIT (links PortAudio, MIT) | Permitted | Notice |
| SpeechRecognition 3.17.0 | BSD-3-Clause | Permitted | Notice. Imports `aifc`/`audioop`, removed from the standard library in Python 3.13 (affects the hardware install only) |
| pyttsx3 2.99 | MPL-2.0 | Permitted; file-level copyleft on modifications to its files | Notice; publish modifications to MPL files if any |
| face_recognition / dlib (optional fallback, not pinned) | Not installed in the verified environment | **Unverified** — check dlib model licences before use | — |

### Optional: cloud (`requirements-cloud.txt`)
| Package | Licence | Notes |
| :--- | :--- | :--- |
| google-genai 2.10.0 | Apache-2.0 | Use of the Gemini API is governed by Google's API terms (data handling, health-related use) — **review** before sending any personal data. MEMORA sends only transcripts for name extraction during identity learning, and only when **both** `MEMORA_ALLOW_CLOUD_LLM=1` and `GEMINI_API_KEY` are set (a key alone does nothing; commit 977d8ff) |

### Development only
pytest 9.1.1 (MIT), ruff 0.14.0 (MIT) — not distributed.

## 3. What can be in a core commercial build today (engineering view)
- **Include:** text conversation, memory, reminders, data controls, diagnostics,
  backup/restore, simulation (all core-permissive).
- **Exclude or license first:** YOLO object detection (AGPL), InsightFace models
  (non-commercial), any face-recognition model whose weight licence is unverified.
- **Review:** Gemini API terms for health-adjacent data; FFmpeg components bundled
  in OpenCV wheels if redistributing binaries.

## 4. Blocked or decision-required items (updated in the remediation mission)
Nothing below has been activated, licensed, or cleared. MEMORA is not legally cleared for
commercial distribution.

| Item | Where it appears | Status | Decision needed |
| :--- | :--- | :--- | :--- |
| `assets/models/scrfd_500m_bnkps.onnx` (InsightFace SCRFD, 2,524,155 bytes, sha256 a3562ef62592bf38…) | tracked in git (public); loaded only by `src/vision/detector.py`, used by the developer diagnostic `--vision-standalone`, which since 5583a4c refuses to run without `--live-hardware`; the main recogniser looks in `assets/` and so does not load it | **Blocked for commercial use** (non-commercial research licence per InsightFace README) | Stop tracking/redistributing (it stays in public history), obtain a commercial licence, or replace |
| InsightFace auto-downloaded models (any `insightface` model zoo use) | `requirements-hardware.txt` path | **Blocked for commercial use** | Same as above |
| `ultralytics` + `yolov8n.pt` | `src/memory/object_ledger.py`; weights local, untracked | **Blocked for closed-source use** (AGPL-3.0; Enterprise licence needed) | Enterprise licence, AGPL compliance, or replacement detector |
| `Systran/faster-whisper-tiny.en` | used by `faster-whisper` (hardware install) | Model card states MIT (converted from openai/whisper-tiny.en). Download is now **off by default** and opt-in via `MEMORA_ALLOW_MODEL_DOWNLOAD=1` (C2-22 closed, 977d8ff) | Decide whether to bundle a pre-downloaded copy with recorded provenance |
| dlib / `face_recognition` models | optional fallback, not installed | **Unverified** | Check model licences before enabling |
| Gemini API | `requirements-cloud.txt`, identity learning only; requires `MEMORA_ALLOW_CLOUD_LLM=1` and a key | **Externally unverified**; API terms not reviewed | Counsel review before sending any personal data |
| `assets/images/banner.png` (1024×1024 JPEG, tracked) | README banner; added in f7f8622 | **Provenance unrecorded** (author, tool or licence unknown) | Record its origin, or replace with an asset of known licence |
| Repository licence | none | **Blocked** | Choose with all contributors' written agreement |
| Deployment paths | Core install and the Docker image include none of the blocked assets (image copies no `assets/`) | Core path has no identified blocker beyond the repository licence | — |

## 5. Evidence that the default build does not depend on restricted assets
- `requirements.txt` contains only the permissive packages in section 2; `insightface`,
  `ultralytics`, `mediapipe`, `onnxruntime`, `faster-whisper` and `google-genai` are in
  optional files only.
- The Docker image copies no `assets/` directory and installs `requirements.txt` only
  (`deployment/docker/Dockerfile`); `.dockerignore` excludes `*.pt`.
- The full test suite and all simulated journeys run in clean environments built from
  `requirements.txt` + `requirements-dev.txt` (Python 3.11 venv; 3.12 and 3.13 containers)
  in which none of the restricted packages is installed — see `docs/RELEASE_GATES.md`
  for the exact commit and commands.
- No default code path downloads model weights (socket-level tests,
  `tests/test_network_policy.py`).

## 6. Repository licence: options for the owner (no choice has been made)
A licence can only be granted by the copyright holders. The history has several
contributors and the project began as a competition entry, so every option below
first needs (a) agreement from all contributors (or assignment) and (b) a check of the
competition terms.

| Option | What it allows others | Fit with current dependencies | Main trade-off |
| :--- | :--- | :--- | :--- |
| Keep "all rights reserved" (no licence; current state) | Viewing only; no right to use, copy or modify | No conflict | Public but unusable by others; collaborators lack clear rights |
| Proprietary licence / commercial EULA (optionally making the repository private) | Only what the owner grants | Requires removing or commercially licensing YOLO (AGPL) and InsightFace models | Code already published stays visible in history and forks |
| Permissive (MIT or Apache-2.0) | Use, modify, sell, incl. closed-source | Core dependencies all compatible; AGPL/non-commercial optional components must stay optional or be replaced | Competitors may reuse the code commercially; Apache-2.0 adds an explicit patent grant |
| Strong copyleft (GPL-3.0 or AGPL-3.0) | Use and modify if derivatives are released under the same licence | AGPL-3.0 is compatible with Ultralytics' AGPL; does not fix InsightFace's non-commercial model terms | Limits closed-source commercial partners; AGPL also covers network use |
| Source-available, non-commercial (e.g. PolyForm Noncommercial) | Study and non-commercial use only | Matches InsightFace model terms | Not an open-source licence; commercial use requires a separate agreement |

Patent note: public disclosure since the repository became public may affect patent
filings for described mechanisms; this is for counsel, not engineering, to assess.

## 7. Recommendations
1. Choose a repository licence or proprietary terms, with all contributors' written agreement.
2. Decide whether to stop tracking `assets/models/scrfd_500m_bnkps.onnx` (it remains in
   public history either way) and how to source a commercially usable face model.
3. Generate a third-party notices file from installed metadata at release time.
4. Have counsel confirm items marked **review** before any distribution or paid pilot.
