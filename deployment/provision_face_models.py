"""
Install owner-supplied YuNet + SFace model files after verifying their published checksums.

    python deployment/provision_face_models.py --from ~/Downloads/opencv-face-models
    python deployment/provision_face_models.py --status

This tool never downloads anything. Obtain the files yourself from
github.com/opencv/opencv_zoo (models/face_detection_yunet, models/face_recognition_sface)
only after reading docs/FACE_RECOGNITION.md: the model files carry MIT / Apache-2.0
licences, but their training data (WIDER FACE; face-recognition datasets) carries
non-commercial terms, and that question is unresolved (docs/LICENSING_REVIEW.md, D3).
Files are copied into MEMORA_FACE_MODEL_DIR (default data/models/face), which git and the
Docker build ignore.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.vision import face_models  # noqa: E402


def provision(source_dir: str, dest_dir: str | None = None) -> list[str]:
    """Copy every recognised, checksum-verified model file from source_dir. Returns installed paths."""
    dest_dir = dest_dir or face_models.model_dir()
    installed, rejected = [], []
    for spec in face_models.MODEL_FILES:
        src = os.path.join(os.path.expanduser(source_dir), spec.filename)
        if not os.path.isfile(src):
            continue
        if os.path.getsize(src) != spec.size or face_models.sha256_of(src) != spec.sha256:
            rejected.append(spec.filename)
            continue
        os.makedirs(dest_dir, exist_ok=True)
        dst = os.path.join(dest_dir, spec.filename)
        tmp = dst + ".tmp"
        shutil.copyfile(src, tmp)
        if face_models.sha256_of(tmp) != spec.sha256:
            os.remove(tmp)
            rejected.append(spec.filename)
            continue
        os.replace(tmp, dst)
        installed.append(dst)
    if rejected:
        raise SystemExit("Rejected (checksum does not match the published file): " + ", ".join(rejected))
    return installed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--from", dest="source", help="folder containing the downloaded .onnx files")
    parser.add_argument("--status", action="store_true", help="report what is installed and verified")
    args = parser.parse_args(argv[1:])
    if args.source:
        for path in provision(args.source):
            print(f"Installed and verified {path}")
    status = face_models.verify_models()
    print(f"Model folder: {face_models.model_dir()}")
    print("Status: " + status.reason())
    if not args.source and not args.status:
        parser.print_help()
    return 0 if status.ready or args.status else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
