#!/usr/bin/env python3
"""Merge scripts/data/capability_i18n.json into sample/caps/*/capability.json (title + summary i18n)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "scripts" / "data" / "capability_i18n.json"
CAPS = ROOT / "sample" / "caps"


def main() -> int:
    if not DATA.is_file():
        print(f"Missing {DATA}", file=sys.stderr)
        return 1
    bundle = json.loads(DATA.read_text(encoding="utf-8"))
    missing: list[str] = []
    for cap_dir in sorted(CAPS.iterdir()):
        if not cap_dir.is_dir() or cap_dir.name.startswith("_"):
            continue
        path = cap_dir / "capability.json"
        if not path.is_file():
            continue
        cap = json.loads(path.read_text(encoding="utf-8"))
        name = cap["capability"]["name"]
        if name not in bundle:
            missing.append(name)
            continue
        cap["capability"]["title"] = bundle[name]["title"]
        cap["capability"]["summary"] = bundle[name]["summary"]
        path.write_text(json.dumps(cap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if missing:
        print("Missing i18n entries:", ", ".join(missing), file=sys.stderr)
        return 1
    print(f"Updated capability.json under {CAPS} from {DATA.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
