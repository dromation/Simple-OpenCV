"""Arbitrary language drafts and the actual external process contract."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from simplemotocam.studio import ROOT, StudioSession, export_python
from simplemotocam.studio_engine import KINDS, StudioPipeline, default_state, demo_frame, validate_state
from simplemotocam.studio_runtime import external_adapters, runtime_catalog


def custom_state(language="rust", code="fn unfinished(", enabled=False):
    state = default_state()
    state["nodes"] = state["nodes"][:2] + [{
        "id": "empty", "kind": "custom", "runtime": language, "enabled": enabled,
        "params": {**KINDS["custom"]["params"], "code": code},
        "codeDrafts": {language: code, "julia": "process(x) = x"},
    }]
    state["view"].update(signal="custom", result="custom")
    return state


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    config = tmp_path / "adapters.json"
    value = {"api": 1, "adapters": {"python-file": {
        "name": "Python file test", "extension": ".py",
        "command": [sys.executable, str(ROOT / "contrib/runtime-adapters/python_file_adapter.py")],
        "backends": ["current", "opencv24"],
    }}}
    config.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setenv("SIMPLEMOTOCAM_RUNTIME_CONFIG", str(config))
    return config, value


def test_unavailable_language_drafts_roundtrip_and_bypass(tmp_path, monkeypatch):
    monkeypatch.delenv("SIMPLEMOTOCAM_RUNTIME_CONFIG", raising=False)
    state = validate_state(custom_state())
    assert state["nodes"][-1]["codeDrafts"]["julia"] == "process(x) = x"
    path = tmp_path / "state.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    restored = validate_state(json.loads(path.read_text(encoding="utf-8")))
    assert restored == state
    values, _ = StudioPipeline(restored).process(demo_frame(0, 24, 20))
    np.testing.assert_array_equal(values["custom"], values["R"])
    restored["nodes"][-1]["enabled"] = True
    with pytest.raises(ValueError, match="compatible"):
        validate_state(restored)


def test_incomplete_python_can_be_saved_but_not_run():
    state = custom_state("python", "def process(")
    validate_state(state)
    state["nodes"][-1]["enabled"] = True
    with pytest.raises(ValueError, match="syntax"):
        validate_state(state)


@pytest.mark.parametrize("drafts", [{"../../bad": "code"}, {"rust": 12}, {"rust": "x" * 20001}])
def test_rejects_malformed_drafts(drafts):
    state = custom_state()
    state["nodes"][-1]["codeDrafts"] = drafts
    with pytest.raises(ValueError):
        validate_state(state)


def test_external_execution_export_and_explicit_run(adapter, tmp_path):
    code = 'def process(c,p):\n    return (c["R"]-c["G"])*p["gain"]'
    state = custom_state("python-file", code, True)
    session = StudioSession(tmp_path / "session", backend="current")
    session.configure(state)
    assert session.frame()["needsCodeRun"]
    assert "stats" in session.frame(run_code=True)
    image = demo_frame(2, 24, 20)
    output, _ = StudioPipeline(state).process(image)
    expected = (image[..., 2].astype(np.float32) - image[..., 1].astype(np.float32)) / 255
    np.testing.assert_allclose(output["custom"], expected, atol=1e-7)
    path = tmp_path / "exported.py"
    source = export_python(state)
    assert str(adapter[0]) not in source  # Trusted host configuration is never embedded.
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("external_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    exported, _ = module.StudioPipeline(module.STATE).process(image)
    np.testing.assert_array_equal(exported["custom"], output["custom"])


@pytest.mark.parametrize("code,match", [
    ('def process(c,p):\n    return np.zeros((1,1))', 'H x W'),
    ('def process(c,p):\n    return c["R"] * np.nan', 'H x W'),
    ('def process(c,p):\n    raise ValueError("adapter failure")', 'adapter failure'),
    ('def process(c,p):\n    while True: pass', 'exceeded'),
])
def test_external_failures_preserve_frame_history(adapter, code, match):
    state = custom_state("python-file", code, True)
    state["nodes"][-1]["params"]["timeout"] = 1
    pipeline = StudioPipeline(state)
    with pytest.raises(ValueError, match=match):
        pipeline.process(demo_frame(0, 20, 20))
    assert pipeline.previous is None


def test_adapter_capabilities_and_configuration(adapter):
    config, value = adapter
    entry = runtime_catalog()["python-file"]
    assert entry["available"] and entry["kinds"] == ["custom"]
    assert "command" not in entry
    value["adapters"]["python-file"]["backends"] = ["opencv24"]
    config.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="compatible"):
        validate_state(custom_state("python-file", "code", True))
    value["adapters"]["python-file"]["command"][0] = "missing-compiler-12345"
    config.write_text(json.dumps(value), encoding="utf-8")
    assert not runtime_catalog()["python-file"]["available"]
    value["adapters"]["python"] = value["adapters"].pop("python-file")
    config.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="replace"):
        external_adapters()
