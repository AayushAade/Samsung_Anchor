# Licensing and Commercial-Readiness Review (engineering notes — not legal advice)

_Updated 2026-10-20. Sources: installed package metadata (`importlib.metadata`) and
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
| SpeechRecognition | 3.17.0 | BSD-3-Clause | Permitted | Notice. Note: imports `aifc`/`audioop`, removed in Python 3.13 |
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
| `yolov8n.pt` (local, git-ignored, not tracked) | Ultralytics weights, AGPL-3.0 per Ultralytics | As above | Do not ship |
| insightface 1.0.1 (code) | README: code under MIT, "no limitation for both academic and commercial usage"; metadata declares no licence | Code permitted | — |
| InsightFace pretrained models, incl. **`assets/models/scrfd_500m_bnkps.onnx` (tracked in git)** | README: training data "and the models trained with these data are available for non-commercial research purposes only"; commercial licensing via InsightFace (contacts listed in their README) | **Non-commercial only.** The file is publicly redistributed by this repository today | Owner decision: stop tracking/redistributing it (history keeps it), obtain a commercial licence, or replace. The main recogniser does not load it (it looks in `assets/`, not `assets/models/`); `src/vision/detector.py` does |
| mediapipe 0.10.35 | Apache-2.0 | Permitted; check bundled model cards | Notice |
| faster-whisper 1.2.1 | MIT | Permitted; Whisper weights downloaded separately (MIT per OpenAI) — **verify at download** | Notice |
| onnxruntime 1.27.0 | MIT | Permitted | Notice |
| PyAudio 0.2.14 | MIT (links PortAudio, MIT) | Permitted | Notice |
| pyttsx3 2.99 | MPL-2.0 | Permitted; file-level copyleft on modifications to its files | Notice; publish modifications to MPL files if any |
| face_recognition / dlib (optional fallback, not pinned) | Not installed in the verified environment | **Unverified** — check dlib model licences before use | — |

### Optional: cloud (`requirements-cloud.txt`)
| Package | Licence | Notes |
| :--- | :--- | :--- |
| google-genai 2.10.0 | Apache-2.0 | Use of the Gemini API is governed by Google's API terms (data handling, health-related use) — **review** before sending any personal data. MEMORA currently sends only transcripts for name extraction during identity learning, and only when `GEMINI_API_KEY` is set |

### Development only
pytest 9.1.1 (MIT), ruff 0.14.0 (MIT) — not distributed.

## 3. What can be in a core commercial build today (engineering view)
- **Include:** text conversation, memory, reminders, data controls, diagnostics,
  backup/restore, simulation (all core-permissive).
- **Exclude or license first:** YOLO object detection (AGPL), InsightFace models
  (non-commercial), any face-recognition model whose weight licence is unverified.
- **Review:** Gemini API terms for health-adjacent data; FFmpeg components bundled
  in OpenCV wheels if redistributing binaries.

## 4. Blocked or decision-required items (final audit, `fafcb78`)
Nothing below has been activated, licensed, or cleared. MEMORA is not legally cleared for
commercial distribution.

| Item | Where it appears | Status | Decision needed |
| :--- | :--- | :--- | :--- |
| `assets/models/scrfd_500m_bnkps.onnx` (InsightFace SCRFD) | tracked in git (public); loaded by `src/vision/detector.py`; the main recogniser looks in `assets/` and so does not load it | **Blocked for commercial use** (non-commercial research licence per InsightFace README) | Stop tracking/redistributing (it stays in public history), obtain a commercial licence, or replace |
| InsightFace auto-downloaded models (any `insightface` model zoo use) | `requirements-hardware.txt` path | **Blocked for commercial use** | Same as above |
| `ultralytics` + `yolov8n.pt` | `src/memory/object_ledger.py`; weights local, untracked | **Blocked for closed-source use** (AGPL-3.0; Enterprise licence needed) | Enterprise licence, AGPL compliance, or replacement detector |
| `Systran/faster-whisper-tiny.en` | fetched from huggingface.co at runtime when `faster-whisper` is installed | Model card states MIT (converted from openai/whisper-tiny.en); **runtime download is undisclosed** (ledger C2-22) | Bundle or pre-download with provenance, or disable by default |
| dlib / `face_recognition` models | optional fallback, not installed | **Unverified** | Check model licences before enabling |
| Gemini API | `requirements-cloud.txt`, identity learning only | **Externally unverified**; API terms not reviewed | Counsel review before sending any personal data |
| Repository licence | none | **Blocked** | Choose with all contributors' written agreement |
| Deployment paths | Core install and the Docker image include none of the blocked assets (image copies no `assets/`) | Core path has no identified blocker beyond the repository licence | — |

## 5. Recommendations
1. Choose a repository licence or proprietary terms, with all contributors' written agreement.
2. Decide whether to stop tracking `assets/models/scrfd_500m_bnkps.onnx` (it remains in
   public history either way) and how to source a commercially usable face model.
3. Generate a third-party notices file from installed metadata at release time.
4. Have counsel confirm items marked **review** before any distribution or paid pilot.
