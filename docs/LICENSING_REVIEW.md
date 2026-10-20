# Licensing Review (engineering notes, not legal advice)

_2026-10-20. Gathered from installed package metadata and repository contents.
Every item marked "review" needs confirmation by qualified counsel before any
commercial distribution._

## Repository
- **The GitHub repository is public** (verified 2026-10-20). Anything committed,
  including the tracked InsightFace model, is publicly redistributed.
- **No LICENSE file.** README states "Samsung Solve For Tomorrow Competition Entry".
  Ownership of contributions by multiple team members and any competition terms
  should be clarified before commercial use — **review**.
- Commit history shows several contributors on the remote `AayushAade/Samsung_Anchor`.

## Core dependencies (requirements.txt)
| Package | Version | Declared licence |
| :--- | :--- | :--- |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| SQLAlchemy | 2.0.51 | MIT |
| faiss-cpu | 1.14.3 | MIT |
| opencv-python | 5.0.0.93 | Apache 2.0 |
| SpeechRecognition | 3.17.0 | BSD-3-Clause |
| psutil | 7.2.2 | BSD-3-Clause |
| pydantic | 2.13.4 | MIT |
| websockets | 16.0 | BSD-3-Clause |

All permissive. Attribution notices are still required when redistributing.

## Optional dependencies
| Package | Version | Declared licence | Note |
| :--- | :--- | :--- | :--- |
| ultralytics | 8.4.87 | **AGPL-3.0** | Network/distribution copyleft; incompatible with closed-source distribution unless an enterprise licence is obtained — **review**. Not on the main path (`src/memory/object_ledger.py`). |
| `yolov8n.pt` (local, untracked) | — | Ultralytics weights, AGPL-3.0 per upstream | **review** |
| insightface | 1.0.1 | none declared in metadata | Upstream states that pretrained models are for non-commercial research use — **review**. |
| `assets/models/scrfd_500m_bnkps.onnx` (**tracked in git**) | — | InsightFace SCRFD model | Same non-commercial concern; consider removing from the repo history before any public/commercial release — **review** |
| mediapipe | 0.10.35 | Apache 2.0 | |
| faster-whisper | 1.2.1 | MIT | Whisper model weights distributed separately — check model licence |
| onnxruntime | 1.27.0 | MIT | |
| PyAudio | 0.2.14 | MIT | |
| pyttsx3 | 2.99 | MPL-2.0 | File-level copyleft on modifications |
| google-genai | 2.10.0 | Apache-2.0 | Gemini API use is governed by Google's API terms (data handling, health use) — **review** |
| torch (transitive) | 2.12.1 | BSD-3-Clause | |

## Recommendations
1. Choose a repository licence (or proprietary terms) with all contributors' agreement.
2. Avoid AGPL and non-commercial model weights in any commercial build; prefer
   permissively licensed detectors/recognisers or obtain commercial licences.
3. Generate a third-party notices file from installed metadata at release time.
