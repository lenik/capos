import json
from pathlib import Path

import pytest

from memcos import MemCOS, PLATFORM_LIFECYCLE_EVENTS


def test_invoke_routes_to_handler():
    cos = MemCOS()
    spec = {
        "module": {
            "id": "a",
            "version": "1.0.0",
            "implements": ["echo.cap"],
        }
    }

    def echo(req):
        return {"ok": True, "in": dict(req)}

    cos.install_module(spec, {"echo.cap": echo})
    out = cos.invoke("echo.cap", {"x": 1})
    assert out["ok"] is True
    assert out["in"] == {"x": 1}


def test_lifecycle_order_and_payload():
    cos = MemCOS()
    spec = {
        "module": {
            "id": "m",
            "version": "2.0.0",
            "implements": ["x.cap"],
            "lifecycle": {"handlesPlatformLifecycle": True},
        }
    }
    seen: list[tuple[str, dict]] = []

    def life(event_name: str, payload):
        seen.append((event_name, dict(payload)))

    cos.install_module(spec, {"x.cap": lambda r: r}, lifecycle=life)
    assert [e for e, _ in seen[:2]] == ["module.preinstall", "module.installed"]
    assert seen[0][1]["moduleId"] == "m"
    cos.remove_module(spec, lifecycle=life)
    tail = [e for e, _ in seen[2:]]
    assert tail == ["module.preremove", "module.removed"]


def test_upgrade_emits_preupgrade_and_upgraded():
    cos = MemCOS()
    spec = {
        "module": {
            "id": "m",
            "version": "2.0.0",
            "implements": ["x.cap"],
            "lifecycle": {"handlesPlatformLifecycle": True},
        }
    }
    events: list[str] = []

    def life(event_name: str, payload):
        events.append(event_name)

    cos.install_module(spec, {"x.cap": lambda r: r}, lifecycle=life)
    events.clear()
    cos.upgrade_module(
        spec,
        {"x.cap": lambda r: {**dict(r), "v": 2}},
        previous_version="1.0.0",
        lifecycle=life,
    )
    assert events[:2] == ["module.preupgrade", "module.upgraded"]


def test_modulespec_example_validates():
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "schemas" / "modulespec.schema.json"
    example = root / "sample" / "modules" / "contactbook" / "modulespec.json"
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    instance = json.loads(example.read_text(encoding="utf-8"))
    jsonschema.validate(instance, schema)


def test_platform_events_tuple_matches_spec():
    assert set(PLATFORM_LIFECYCLE_EVENTS) == {
        "module.preinstall",
        "module.installed",
        "module.preremove",
        "module.removed",
        "module.preupgrade",
        "module.upgraded",
    }
