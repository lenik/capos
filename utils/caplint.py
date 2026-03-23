#!/usr/bin/env python3
"""caplint — validate capability.json files under sample/caps/ against schemas/capspec.schema.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def lint_caps(
    repo_root: Path | None = None,
    *,
    verbose: bool = False,
) -> tuple[int, list[str]]:
    repo_root = repo_root or REPO
    samples = repo_root / "sample" / "caps"
    schema_path = repo_root / "schemas" / "capspec.schema.json"
    if not schema_path.is_file():
        return 1, [f"Missing schema: {schema_path}"]
    try:
        import jsonschema
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema", "-q"])
        import jsonschema

    cap_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    count = 0
    if not samples.is_dir():
        return 1, [f"Missing capability sample directory: {samples}"]
    for d in sorted(samples.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        cap_file = d / "capability.json"
        if not cap_file.is_file():
            continue
        count += 1
        data = json.loads(cap_file.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=data, schema=cap_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{cap_file}: {e.message}")
            if verbose:
                errors.append(f"  at json path: {list(e.absolute_path)}")
    return len(errors), errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate CapSpec capability.json files.")
    p.add_argument(
        "--root",
        type=Path,
        default=REPO,
        help="Repository root (default: parent of utils/)",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    n_err, msgs = lint_caps(args.root, verbose=args.verbose)
    for m in msgs:
        print(m, file=sys.stderr)
    if n_err == 0:
        samples = args.root / "sample" / "caps"
        n = sum(
            1
            for d in samples.iterdir()
            if d.is_dir() and not d.name.startswith("_") and (d / "capability.json").is_file()
        )
        print(f"caplint: OK ({n} capability.json files under {samples})")
    return 1 if n_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
