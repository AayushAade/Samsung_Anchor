"""
Face-recognition model files for the OpenCV YuNet + SFace backend.

MEMORA never downloads these files and does not ship them (they are not tracked in git
and not copied into the Docker image). The owner provisions them explicitly
(`python deployment/provision_face_models.py --from DIR`), and they are used only when
their SHA-256 matches the published value below. Licences and training-data caveats:
docs/LICENSING_REVIEW.md (decision D3) and docs/FACE_RECOGNITION.md.

Checksums are the Git LFS object ids published in github.com/opencv/opencv_zoo
(read 2026-10-21).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional

from config import settings


@dataclass(frozen=True)
class ModelFile:
    role: str            # "detector" | "recognizer"
    filename: str
    sha256: str
    size: int
    licence: str
    source: str


# Accepted files, in order of preference for each role.
MODEL_FILES: tuple[ModelFile, ...] = (
    ModelFile("detector", "face_detection_yunet_2026may.onnx",
              "ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0", 229738, "MIT",
              "opencv_zoo/models/face_detection_yunet"),
    ModelFile("detector", "face_detection_yunet_2023mar.onnx",
              "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4", 232589, "MIT",
              "opencv_zoo/models/face_detection_yunet"),
    ModelFile("recognizer", "face_recognition_sface_2021dec.onnx",
              "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79", 38696353, "Apache-2.0",
              "opencv_zoo/models/face_recognition_sface"),
)


def model_dir() -> str:
    """Where provisioned model files live (git-ignored, outside the Docker build context)."""
    return os.environ.get("MEMORA_FACE_MODEL_DIR") or os.path.join(str(settings.BASE_DIR), "data", "models", "face")


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class ModelStatus:
    detector: Optional[str]      # verified path or None
    recognizer: Optional[str]
    problems: list[str]

    @property
    def ready(self) -> bool:
        return self.detector is not None and self.recognizer is not None

    def reason(self) -> str:
        if self.ready:
            return "YuNet + SFace models verified"
        return "; ".join(self.problems)


def verify_models(directory: Optional[str] = None) -> ModelStatus:
    """Check provisioned files by size and SHA-256. Never downloads anything."""
    directory = directory or model_dir()
    found: dict[str, Optional[str]] = {"detector": None, "recognizer": None}
    problems: list[str] = []
    for role in ("detector", "recognizer"):
        candidates = [m for m in MODEL_FILES if m.role == role]
        for spec in candidates:
            path = os.path.join(directory, spec.filename)
            if not os.path.isfile(path):
                continue
            if os.path.getsize(path) != spec.size or sha256_of(path) != spec.sha256:
                problems.append(f"{spec.filename} does not match its published checksum")
                continue
            found[role] = path
            break
        if found[role] is None and not any(spec.filename in p for spec in candidates for p in problems):
            names = " or ".join(s.filename for s in candidates)
            problems.append(f"{role} model not provisioned ({names} in {directory})")
    return ModelStatus(found["detector"], found["recognizer"], problems)
