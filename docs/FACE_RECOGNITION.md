# Face Recognition — Backend Decision and Status

_2026-10-21. Status: **implemented and tested with synthetic stand-ins; NOT active by
default; model files NOT provided; NOT tested on a real camera or real faces.**_

## 1. The problem
Before this work, the pinned hardware install had no working face-recognition backend. dlib
`face_recognition` was not installed; the "insightface" backend had no detection or embedding
code; MediaPipe 0.10.35 lacks the legacy FaceMesh API. The recogniser also fabricated faces
from real frames when nothing was available (fixed in `b00922f`; it now reports
`unavailable`).

## 2. Options (evidence gathered 2026-10-21)
| Criterion | OpenCV YuNet + SFace | dlib `face_recognition` | InsightFace (buffalo / SCRFD + ArcFace) |
| :--- | :--- | :--- | :--- |
| Code in MEMORA | **Implemented** (`sface` backend) | Branch exists, never runnable here | Detector class only; no recognition code |
| Extra Python packages | **None**: `cv2.FaceDetectorYN` / `cv2.FaceRecognizerSF` are in the pinned core `opencv-python` 5.0.0 (checked on Python 3.11 locally; same wheel family in CI for 3.12/3.13) | `dlib` 20.0.1 is **source-only** on PyPI (needs a C++ toolchain and cmake); `face_recognition` 1.3.0, last released 2020-02-20 | `insightface` + `onnxruntime` (hardware extras) |
| Model weights licence (publisher) | YuNet: "licensed under MIT License"; SFace: "licensed under Apache 2.0 License" (opencv_zoo) | `dlib_face_recognition_resnet_model_v1`: public domain / CC0 (dlib-models) | "non-commercial research purposes only" (InsightFace README) |
| Training data | YuNet: WIDER FACE (libfacedetection.train), whose dataset card declares **CC BY-NC-ND 4.0**. SFace: not stated by OpenCV; the SFace authors' models were trained on CASIA-WebFace, VGGFace2 and MS-Celeb-1M (all research-only; MS-Celeb-1M withdrawn by Microsoft) | Web-collected face images (dlib author); details not verified here | Non-commercial datasets (stated by InsightFace) |
| Model size | ~230 KB + ~38.7 MB | ~22 MB | varies |
| Runs on CPU, macOS arm64 | Yes (OpenCV) | Yes after compilation | Yes |

**Decision (engineering): OpenCV YuNet + SFace.** It is the only option that needs no new
dependency, installs on every supported Python, and was implementable and testable now. The
decision is not based on its weights licence alone: every option's weights were trained on
face datasets with non-commercial or uncertain terms. **Whether those terms affect use of
the trained weights is a legal question for counsel (decision D3).** Until it is answered,
MEMORA neither ships nor downloads the models; the owner provisions them deliberately.

## 3. What is implemented
- `src/vision/face_models.py`: accepted files with **pinned SHA-256 and sizes** (the Git LFS
  object ids published in opencv_zoo):
  | File | SHA-256 | Bytes |
  | :--- | :--- | :--- |
  | `face_detection_yunet_2026may.onnx` (preferred; dynamic input) | `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0` | 229,738 |
  | `face_detection_yunet_2023mar.onnx` | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | 232,589 |
  | `face_recognition_sface_2021dec.onnx` | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | 38,696,353 |
- `deployment/provision_face_models.py --from DIR`: copies owner-supplied files into
  `MEMORA_FACE_MODEL_DIR` (default `data/models/face`, ignored by git and Docker) only if size
  and SHA-256 match. **No download code exists.**
- `MemoraFaceRecognizer` backend `sface`, selected only with `--live-hardware` (real frames)
  and verified models:
  - YuNet detection; detections scoring below `FACE_DETECTION_MIN_SCORE` (0.8) or smaller than
    `FACE_MIN_SIZE_PX` (60 px) are ignored.
  - **No embedding is computed without `faces` consent**; faces are only located and labelled
    "Face recognition is off".
  - SFace alignment and 128-D features, L2-normalised; matched by L2 distance against the
    per-database vector store with `SFACE_MATCH_TOLERANCE` = 1.0. That is stricter than
    OpenCV's published LFW threshold of 1.128, because naming the wrong person is worse than
    not recognising someone.
  - **Ambiguity:** if a second, different person is within tolerance and within
    `SFACE_AMBIGUITY_MARGIN` (0.08) of the best match, the face is labelled
    "Not sure who this is" and is neither named nor enrolled.
  - New faces become anonymous people only after 15 stable frames, re-checked against stored
    people first (no duplicate enrolment). Names come only from identity learning, which needs
    `memory` + `faces` consent at the storage layer; a confirmed name is never renamed by
    speech (`8296de8`).
  - Deletion: `/delete-all` and identity deletion remove embeddings; a deleted person is not
    recognised again.
  - If models are missing, mismatched or cannot be loaded by OpenCV, the backend is
    `unavailable` with the reason: shown by `--check` ("Face Recognition Models") and the
    runtime status ("Face Recognition: FAILED (…)"). There are never simulated detections on
    real frames.
- Tests: `tests/test_face_recognition_sface.py` (15) drives `process_frame` end to end with
  stand-in OpenCV objects. Mutation checks confirmed the consent and ambiguity tests fail when
  that logic is removed.

## 4. Not verified
- That OpenCV 5.0.0 loads and runs these exact model files (the 2026may YuNet file targets
  OpenCV 5's ONNX Runtime engine; the 2023mar file has a fixed input shape). The files were
  not downloaded: the owner must approve the download, and the training-data question is open.
- Accuracy, false-match rates and thresholds on real cameras, lighting, ages and skin tones
  (fairness has not been assessed).
- Live operation with a camera.

## 5. To try it (owner decision; not done)
1. Decide D3 (counsel: training-data terms; biometric-privacy review).
2. Download the three files from opencv_zoo yourself into a folder, then
   `python deployment/provision_face_models.py --from <folder>`.
3. `python app.py --check`: expect "Face Recognition Models: PASS".
4. Follow `docs/HARDWARE_TEST_CHECKLIST.md` §2 with consenting adults only.
