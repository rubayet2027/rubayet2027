#!/usr/bin/env python3
"""Validate the profile README's assets.

Two checks, both stdlib-only so this runs anywhere (local shell or CI):

1. Every SVG under assets/ and cards/ is non-empty, well-formed XML.
2. Every repo-relative path referenced by README.md (src/href) exists on disk.

External links (http/https/mailto/data URIs) are ignored. Exits non-zero if
anything is broken.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
SVG_DIRS = [ROOT / "assets", ROOT / "cards"]
EXTERNAL_PREFIXES = ("http://", "https://", "data:", "mailto:", "tel:", "#")


def check_svgs():
    errors = []
    svgs = []
    for d in SVG_DIRS:
        if d.is_dir():
            svgs.extend(sorted(d.rglob("*.svg")))
    for path in svgs:
        rel = path.relative_to(ROOT)
        try:
            if path.stat().st_size == 0:
                raise ValueError("file is empty")
            ET.parse(path)
            print(f"  ok   {rel}")
        except Exception as exc:
            print(f"  FAIL {rel}: {exc}")
            errors.append(f"{rel}: {exc}")
    print(f"{len(svgs)} SVG(s) checked, {len(errors)} invalid")
    return errors


def check_readme_paths():
    errors = []
    md = README.read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="([^"]+)"', md)
    local = [
        r for r in refs
        if not r.startswith(EXTERNAL_PREFIXES) and r.strip()
    ]
    for ref in local:
        clean = ref.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        if (ROOT / clean).exists():
            print(f"  ok   {ref}")
        else:
            print(f"  FAIL {ref} (referenced in README.md, not found)")
            errors.append(ref)
    print(f"{len(local)} local reference(s) checked, {len(errors)} missing")
    return errors


def main():
    print("Validating SVG assets ...")
    svg_errors = check_svgs()
    print("\nValidating README.md asset paths ...")
    path_errors = check_readme_paths()

    total = len(svg_errors) + len(path_errors)
    if total:
        print(f"\n{total} problem(s) found.")
        return 1
    print("\nAll assets valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
