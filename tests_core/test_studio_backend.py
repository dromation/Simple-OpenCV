import copy
import importlib.util
import json
import shutil
import subprocess
import cv2
import numpy as np
import pytest
from simplemotocam.studio_backend import backend_catalog, opencv24_worker, CV24_NATIVE
from simplemotocam.studio_engine import (
    KINDS,
    StudioPipeline,
    default_state,
    validate_state,
    demo_frame,
)
from simplemotocam.studio import StudioSession, export_python

legacy = pytest.mark.skipif(
    not backend_catalog()["opencv24"]["available"],
    reason="Build the optional OpenCV 2.4 worker",
)


def state_for(kind):
    state = default_state()
    state["nodes"] = state["nodes"][:2]
    params = copy.deepcopy(KINDS[kind]["params"])
    params["input"] = "R"
    state["nodes"].append(
        {"id": "operation", "kind": kind, "enabled": True, "params": params}
    )
    state["view"].update(signal="R", result=params["output"])
    state["backend"] = {"id": "opencv24", "version": "2.4.13.7"}
    return state


def test_old_states_stay_on_current_engine():
    old = default_state()
    old.pop("backend", None)
    assert validate_state(old)["backend"] == {
        "id": "current",
        "version": cv2.__version__,
    }


def test_missing_engine_never_falls_back(monkeypatch, tmp_path):
    monkeypatch.setenv("SIMPLEMOTOCAM_OPENCV24_WORKER", str(tmp_path / "missing.exe"))
    assert not backend_catalog()["opencv24"]["available"]
    with pytest.raises(ValueError, match="missing or outdated"):
        validate_state(state_for("gaussian"))
    assert validate_state(default_state())["backend"]["id"] == "current"


def test_version_mismatch_is_explicit():
    state = default_state()
    state["backend"] = {"id": "current", "version": "0.0.0"}
    with pytest.raises(ValueError, match="differs"):
        validate_state(state)


@legacy
@pytest.mark.parametrize("kind", sorted(CV24_NATIVE))
def test_real_legacy_operations(kind):
    state = state_for(kind)
    image = demo_frame(3, 160, 120)
    values, _ = StudioPipeline(state).process(image)
    result = values[state["view"]["result"]]
    assert (
        result.shape == (120, 160)
        and result.dtype == np.float32
        and np.isfinite(result).all()
    )
    if kind in ("threshold", "canny", "otsu", "adaptive", "hough"):
        assert set(np.unique(result)) <= {0, 1}


@legacy
def test_worker_version_and_no_current_filter_calls(monkeypatch):
    assert (
        subprocess.check_output(
            [str(opencv24_worker()), "--version"], text=True
        ).strip()
        == "2.4.13.7"
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("OpenCV 4 was called instead of 2.4")

    monkeypatch.setattr(cv2, "GaussianBlur", forbidden)
    monkeypatch.setattr(cv2, "getDerivKernels", forbidden)
    state = default_state()
    state["backend"] = {"id": "opencv24"}
    pipeline = StudioPipeline(state)
    pipeline.process(demo_frame(0, 160, 120))
    values, _ = pipeline.process(demo_frame(1, 160, 120))
    assert values["edges"].max() > 0


@legacy
@pytest.mark.parametrize(
    "kind",
    [
        "gaussian",
        "box",
        "median",
        "kernel",
        "sobel",
        "scharr",
        "laplacian",
        "threshold",
        "erode",
        "dilate",
        "opening",
        "closing",
        "morph_gradient",
        "bilateral",
    ],
)
def test_numeric_comparison_with_current_on_same_input(kind):
    image = np.random.default_rng(13).integers(10, 230, (31, 37, 3), dtype=np.uint8)
    state = state_for(kind)
    old, _ = StudioPipeline(state).process(image)
    current = copy.deepcopy(state)
    current["backend"] = {"id": "current"}
    new, _ = StudioPipeline(current).process(image)
    output = state["view"]["result"]
    np.testing.assert_allclose(old[output], new[output], atol=2e-6, rtol=2e-6)


@legacy
def test_saved_profile_export_and_history(tmp_path):
    state = default_state()
    state["backend"] = {"id": "opencv24"}
    session = StudioSession(tmp_path, backend="current")
    session.frame()
    session.configure(state)
    assert session.pipeline.previous is None
    assert session.frame()["backend"]["version"] == "2.4.13.7"
    saved = session.save(session.state)
    assert saved["state"]["backend"] == {"id": "opencv24", "version": "2.4.13.7"}
    exported = tmp_path / "exported.py"
    exported.write_text(export_python(session.state), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("legacy_export", exported)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = StudioPipeline(session.state)
    restored = module.StudioPipeline(module.STATE)
    for index in range(3):
        image = demo_frame(index, 160, 120)
        expected, _ = original.process(image)
        actual, _ = restored.process(image)
        for channel in expected:
            np.testing.assert_array_equal(expected[channel], actual[channel])
    changed = copy.deepcopy(session.state)
    changed["backend"] = {"id": "current"}
    session.configure(changed)
    assert session.pipeline.previous is None


@legacy
def test_primary_engine_and_explicit_current(tmp_path, monkeypatch):
    monkeypatch.delenv("SIMPLEMOTOCAM_DEFAULT_BACKEND", raising=False)
    assert StudioSession(tmp_path).state["backend"]["id"] == "opencv24"
    assert (
        StudioSession(tmp_path, backend="current").state["backend"]["id"] == "current"
    )
    monkeypatch.setenv("SIMPLEMOTOCAM_OPENCV24_WORKER", str(tmp_path / "missing.exe"))
    with pytest.raises(ValueError, match="missing or outdated"):
        StudioSession(tmp_path)


@legacy
def test_components_exact_holes_diagonals_and_thresholds():
    from simplemotocam.studio_backend import run_opencv24

    for seed in range(5):
        plane = (np.random.default_rng(seed).random((30, 40)) > 0.7).astype(np.float32)
        plane[4:12, 4:12] = 1
        plane[6:10, 6:10] = 0
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            plane.astype(np.uint8), 8
        )
        for area in (1, 5, 30, 80):
            keep = np.zeros(count, np.float32)
            keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= area
            np.testing.assert_array_equal(
                run_opencv24("components", plane, {"minArea": area}), keep[labels]
            )


@legacy
def test_custom_legacy_native_and_export(tmp_path):
    state = state_for("custom")
    state["nodes"][-1]["params"][
        "code"
    ] = 'def process(c,p):\n    import cv2\n    assert cv2.__version__ == "2.4.13.7"\n    return cv24.run("gaussian", c["R"]-c["G"], size=3, sigma=1)'
    image = demo_frame(1, 80, 60)
    actual, _ = StudioPipeline(state).process(image)
    from simplemotocam.studio_backend import run_opencv24

    expected = run_opencv24(
        "gaussian", actual["R"] - actual["G"], {"size": 3, "sigma": 1}
    )
    np.testing.assert_array_equal(actual["custom"], expected)
    exported = tmp_path / "legacy_custom.py"
    exported.write_text(export_python(state), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("legacy_custom", exported)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    restored, _ = module.StudioPipeline(module.STATE).process(image)
    np.testing.assert_array_equal(restored["custom"], expected)
    state["nodes"][-1]["params"][
        "code"
    ] = 'def process(c,p):\n    import cv2\n    return cv2.GaussianBlur(c["R"], (3,3), 1)'
    with pytest.raises(ValueError, match="not the full legacy"):
        StudioPipeline(state).process(image)


@legacy
@pytest.mark.skipif(not shutil.which("node"), reason="Optional Node.js runtime")
def test_javascript_choice_is_honored_under_legacy_profile(monkeypatch):
    import simplemotocam.studio_engine as engine

    def forbidden(*args, **kwargs):
        raise AssertionError("Native worker ignored JavaScript language choice")

    monkeypatch.setattr(engine, "run_opencv24", forbidden)
    state = state_for("threshold")
    state["nodes"][-1]["runtime"] = "javascript"
    values, _ = StudioPipeline(state).process(demo_frame(0, 20, 20))
    assert set(np.unique(values["mask"])) <= {0, 1}
