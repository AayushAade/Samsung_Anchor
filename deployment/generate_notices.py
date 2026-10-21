"""
Write third-party licence notices and a CycloneDX SBOM for the Python environment it runs in.

    python deployment/generate_notices.py OUTPUT_DIR

Creates OUTPUT_DIR/THIRD_PARTY_NOTICES.txt (every installed distribution with its version,
declared licence and the full text of each licence/notice file it ships, e.g. OpenCV's
LICENSE-3RD-PARTY.txt for bundled FFmpeg/Qt) and OUTPUT_DIR/sbom.cdx.json. Reads package
metadata only; no network access. The Docker image runs it at build time.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from importlib import metadata

# An SPDX-looking expression (ids joined by AND/OR/WITH); anything else is recorded as a name.
_SPDX = re.compile(r"^[A-Za-z0-9.+\-]+( (AND|OR|WITH) [A-Za-z0-9.+\-]+)*$")
LICENCE_FILE = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE|AUTHORS)[^/]*$", re.IGNORECASE)


def _declared_licence(md) -> str:
    expr = md.get("License-Expression")
    if expr:
        return expr
    classifiers = [c.split("::")[-1].strip() for c in (md.get_all("Classifier") or []) if c.startswith("License ::")]
    raw = (md.get("License") or "").strip()
    if raw and len(raw) < 80 and "\n" not in raw:
        return raw
    return "; ".join(classifiers) or "UNKNOWN (see licence files)"


def collect() -> list[dict]:
    seen, out = set(), []
    for dist in sorted(metadata.distributions(), key=lambda d: (d.metadata["Name"] or "").lower()):
        name = dist.metadata["Name"]
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        files = []
        for f in dist.files or []:
            if LICENCE_FILE.search(str(f)):
                try:
                    files.append((str(f), f.locate().read_bytes().decode("utf-8", errors="replace")))
                except (OSError, ValueError):
                    files.append((str(f), "(could not be read)"))
        out.append({"name": name, "version": dist.version, "licence": _declared_licence(dist.metadata),
                    "files": files})
    return out


def write(output_dir: str) -> tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    packages = collect()
    notices = os.path.join(output_dir, "THIRD_PARTY_NOTICES.txt")
    with open(notices, "w", encoding="utf-8") as f:
        f.write("Third-party software in this MEMORA environment\n"
                f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} with Python "
                f"{sys.version.split()[0]}. Engineering record, not legal advice.\n\n")
        for p in packages:
            f.write(f"{p['name']} {p['version']} — {p['licence']}\n")
        for p in packages:
            for path, text in p["files"]:
                f.write(f"\n{'=' * 78}\n{p['name']} {p['version']}: {path}\n{'=' * 78}\n{text}\n")
    sbom = os.path.join(output_dir, "sbom.cdx.json")
    with open(sbom, "w", encoding="utf-8") as f:
        json.dump({
            "bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
            "metadata": {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "component": {"type": "application", "name": "memora"}},
            "components": [{"type": "library", "name": p["name"], "version": p["version"],
                            "purl": f"pkg:pypi/{p['name'].lower()}@{p['version']}",
                            "licenses": [{"expression": p["licence"]}] if _SPDX.match(p["licence"])
                            else [{"license": {"name": p["licence"]}}]}
                           for p in packages],
        }, f, indent=2)
    return notices, sbom


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.strip())
        sys.exit(2)
    for path in write(sys.argv[1]):
        print(f"Wrote {path}")
