"""Run CapSpec test cases (YAML) against a capability implementation (unit-test oriented)."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Callable

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*RefResolver is deprecated.*")

InvokeFn = Callable[[str, dict[str, Any]], dict[str, Any]]
AdapterFactory = Callable[[], InvokeFn]


class CapError(Exception):
    """Business / contract error raised by implementations (maps to CapSpec error.code)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
        import yaml

    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validator_for_schema(schema_path: Path):
    from jsonschema import Draft202012Validator
    from jsonschema.validators import RefResolver

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    base = schema_path.parent.resolve()
    resolver = RefResolver(base_uri=base.as_uri() + "/", referrer=schema)
    return Draft202012Validator(schema, resolver=resolver)


def run_capability_cases(
    capability_dir: Path,
    invoke: InvokeFn,
    *,
    capability_name: str | None = None,
) -> list[str]:
    """
    Execute tests from tests/contract-tests.yaml plus optional tests.caseFiles (cases: [...]).
    Returns a list of failure messages (empty if all passed).
    """
    cap_json = capability_dir / "capability.json"
    if not cap_json.is_file():
        return [f"Missing {cap_json}"]
    cap = json.loads(cap_json.read_text(encoding="utf-8"))
    name = capability_name or cap["capability"]["name"]
    failures: list[str] = []

    def run_case_file(yaml_path: Path, use_tests_key: bool) -> None:
        if not yaml_path.is_file():
            failures.append(f"Missing test file: {yaml_path}")
            return
        doc = _load_yaml(yaml_path)
        key = "tests" if use_tests_key else "cases"
        items = doc.get(key) or []
        for t in items:
            failures.extend(_run_one_case(capability_dir, cap, name, invoke, t))

    run_case_file(capability_dir / "tests" / "contract-tests.yaml", use_tests_key=True)
    tests_meta = cap.get("tests") or {}
    for rel in tests_meta.get("caseFiles") or []:
        run_case_file(capability_dir / rel, use_tests_key=False)

    return failures


def _run_one_case(
    capability_dir: Path,
    cap: dict,
    name: str,
    invoke: InvokeFn,
    t: dict,
) -> list[str]:
    failures: list[str] = []
    case_name = t.get("name", "?")
    sig = cap["signature"]
    model = sig.get("model")
    req = t.get("request") or t.get("event") or {}
    try:
        if model == "query-execution":
            # Test files use "request" for query payload
            result = invoke(name, req)
        elif model == "event-handler":
            result = invoke(name, req)
        else:
            result = invoke(name, req)
    except CapError as e:
        if "expectError" in t:
            exp = t["expectError"]
            if exp.get("code") != e.code:
                failures.append(f"{case_name}: expected error {exp.get('code')}, got {e.code}")
            return failures
        failures.append(f"{case_name}: unexpected CapError {e.code}: {e.message}")
        return failures
    except Exception as e:
        failures.append(f"{case_name}: invoke raised {type(e).__name__}: {e}")
        return failures

    if "expectError" in t:
        failures.append(f"{case_name}: expected error {t['expectError']}, got success")
        return failures

    if "expect" in t:
        exp = t["expect"]
        if exp.get("status") == "success" and result is None:
            failures.append(f"{case_name}: expected success with body, got None")
        # Optional: shallow check keys in expect.response subset — keep minimal

    resp_rel = sig.get("responseSchema")
    if resp_rel and result is not None:
        resp_path = capability_dir / resp_rel
        if resp_path.is_file():
            try:
                v = _validator_for_schema(resp_path)
                v.validate(result)
            except Exception as e:
                failures.append(f"{case_name}: response schema: {e}")
    return failures


def run_capabilities_matching(
    caps_root: Path,
    adapter_factory: AdapterFactory,
    name_prefix: str,
) -> list[str]:
    """Run all capabilities under caps_root (e.g. sample/caps) whose name starts with name_prefix.

    ``adapter_factory`` is called once per capability directory so destructive tests
    in one cap do not break the next (each gets a fresh adapter instance).
    """
    all_failures: list[str] = []
    for d in sorted(caps_root.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        cap_file = d / "capability.json"
        if not cap_file.is_file():
            continue
        cap = json.loads(cap_file.read_text(encoding="utf-8"))
        n = cap["capability"]["name"]
        if not n.startswith(name_prefix):
            continue
        invoke = adapter_factory()
        fails = run_capability_cases(d, invoke, capability_name=n)
        for f in fails:
            all_failures.append(f"{n}: {f}")
    return all_failures
