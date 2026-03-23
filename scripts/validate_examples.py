#!/usr/bin/env python3
"""Validate examples/success.json request/response payloads against each module's JSON Schemas."""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"


def main() -> int:
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.validators import RefResolver
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema", "-q"])
        from jsonschema import Draft202012Validator
        from jsonschema.validators import RefResolver

    errors = 0
    checked = 0
    modules = 0
    for d in sorted(MODULES.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        success = d / "examples" / "success.json"
        if not success.is_file():
            continue
        cap = json.loads((d / "capability.json").read_text(encoding="utf-8"))
        sig = cap["signature"]
        model = sig.get("model")
        if model == "query-execution":
            in_rel = sig.get("querySchema")
        elif model == "event-handler":
            in_rel = sig.get("eventSchema")
        else:
            in_rel = sig.get("requestSchema")
        out_rel = sig.get("responseSchema")
        if not in_rel:
            continue
        ex = json.loads(success.read_text(encoding="utf-8"))
        in_path = d / in_rel
        out_path = d / out_rel if out_rel else None
        modules += 1
        payload = None
        if model == "event-handler":
            payload = ex.get("event") if "event" in ex else ex.get("request")
        else:
            payload = ex.get("request")
        if payload is not None and in_path.is_file():
            schema = json.loads(in_path.read_text(encoding="utf-8"))
            base = in_path.parent.resolve()
            resolver = RefResolver(base_uri=base.as_uri() + "/", referrer=schema)
            try:
                Draft202012Validator(schema, resolver=resolver).validate(payload)
            except Exception as e:
                errors += 1
                label = "event" if model == "event-handler" else "request"
                print(f"{success}: {label}: {e}", file=sys.stderr)
            checked += 1
        if out_path and out_path.is_file() and "response" in ex:
            schema = json.loads(out_path.read_text(encoding="utf-8"))
            base = out_path.parent.resolve()
            resolver = RefResolver(base_uri=base.as_uri() + "/", referrer=schema)
            try:
                Draft202012Validator(schema, resolver=resolver).validate(ex["response"])
            except Exception as e:
                errors += 1
                print(f"{success}: response: {e}", file=sys.stderr)
            checked += 1
    print(f"Validated success examples in {modules} modules ({checked} schema checks), {errors} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
