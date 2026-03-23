#!/usr/bin/env python3
"""Validate every modules/*/capability.json against schemas/capspec.schema.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        import jsonschema
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema", "-q"])
        import jsonschema

    cap_schema = json.loads((ROOT / "schemas" / "capspec.schema.json").read_text(encoding="utf-8"))
    mods = ROOT / "modules"
    errors = 0
    count = 0
    for d in sorted(mods.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        cap_path = d / "capability.json"
        if not cap_path.is_file():
            continue
        count += 1
        data = json.loads(cap_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=data, schema=cap_schema)
        except jsonschema.ValidationError as e:
            errors += 1
            print(f"{cap_path}: {e.message}", file=sys.stderr)
    print(f"Validated {count} capability.json files, {errors} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
