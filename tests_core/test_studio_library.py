import copy
import importlib.util
import shutil
import time
from pathlib import Path
import cv2
import numpy as np
import pytest
from simplemotocam.studio_engine import (
    KINDS,
    StudioPipeline,
    default_state,
    validate_state,
    demo_frame,
)
from simplemotocam.studio_runtime import runtime_catalog
from simplemotocam.studio_catalog import library_catalog, save_library_block
from simplemotocam.studio import StudioSession, export_python


def state_for(kind, runtime="python", **params):
    state = default_state()
    state["nodes"] = state["nodes"][:2] + [
        {
            "id": "operation",
            "kind": kind,
            "runtime": runtime,
            "enabled": True,
            "params": {**copy.deepcopy(KINDS[kind]["params"]), **params},
        }
    ]
    if "input" in state["nodes"][-1]["params"]:
        state["nodes"][-1]["params"]["input"] = "R"
    state["view"].update(signal="R", result=state["nodes"][-1]["params"]["output"])
    return state


def result(state, image=None):
    values, _ = StudioPipeline(state).process(
        demo_frame(4, 160, 120) if image is None else image
    )
    return values[state["view"]["result"]]


@pytest.mark.parametrize(
    "kind", [k for k in KINDS if k not in ("source", "channels", "difference")]
)
def test_registered_blocks_produce_finite_planes(kind):
    state = state_for(kind, **({"expression": "R-G"} if kind == "algebra" else {}))
    value = result(state)
    assert (
        value.shape == (120, 160)
        and value.dtype == np.float32
        and np.isfinite(value).all()
    )


def test_new_numerical_contracts():
    image = np.zeros((32, 32, 3), np.uint8)
    image[4:18, 5:20, 2] = 255
    image[25, 25, 2] = 255
    plane = image[:, :, 2].astype(np.float32) / 255
    kernel = np.ones((3, 3), np.uint8)
    expected = {
        "invert": 1 - plane,
        "luminance": plane * 0.299,
        "color_distance": plane / np.sqrt(3),
        "box": cv2.blur(plane, (3, 3)),
        "laplacian": cv2.Laplacian(plane, cv2.CV_32F, ksize=1),
        "canny": cv2.Canny(image[:, :, 2], 50, 100, L2gradient=True) / 255,
        "otsu": plane,
        "adaptive": cv2.adaptiveThreshold(
            image[:, :, 2],
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        / 255,
        "bilateral": cv2.bilateralFilter(plane, 5, 0.1, 1.2),
    }
    for name, op in [
        ("erode", cv2.MORPH_ERODE),
        ("dilate", cv2.MORPH_DILATE),
        ("opening", cv2.MORPH_OPEN),
        ("closing", cv2.MORPH_CLOSE),
        ("morph_gradient", cv2.MORPH_GRADIENT),
    ]:
        expected[name] = cv2.morphologyEx(plane, op, kernel)
    expected["components"] = plane.copy()
    expected["components"][25, 25] = 0
    for kind, value in expected.items():
        np.testing.assert_allclose(
            result(state_for(kind), image), value, atol=1e-6, err_msg=kind
        )
    # Hough must return actual detected line pixels, not the source mask.
    line_image = np.zeros_like(image)
    line_image[16, 2:30, 2] = 255
    lines = result(state_for("hough", votes=10, minLength=10, maxGap=0), line_image)
    assert lines[16, 2:30].sum() >= 20 and lines.sum() <= 28


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js optional adapter")
@pytest.mark.parametrize("kind", ["invert", "luminance", "threshold", "color_distance"])
def test_language_numerical_parity(kind):
    image = np.random.default_rng(7).integers(0, 256, (17, 23, 3), dtype=np.uint8)
    np.testing.assert_allclose(
        result(state_for(kind, "javascript"), image),
        result(state_for(kind), image),
        atol=2e-7,
    )


@pytest.mark.parametrize(
    "language,code",
    [
        (
            "python",
            'def process(channels, params):\n    return (channels["R"]-channels["G"])*params["gain"]',
        ),
        (
            "javascript",
            "function process(c,p,shape){return c.R.map((r,i)=>(r-c.G[i])*p.gain);}",
        ),
    ],
)
def test_custom_code_and_standalone_export(language, code, tmp_path):
    if language == "javascript" and not shutil.which("node"):
        pytest.skip("Node.js optional")
    state = state_for("custom", language, code=code, gain=2.5)
    image = demo_frame(3, 40, 30)
    expected = (
        (image[:, :, 2].astype(np.float32) - image[:, :, 1].astype(np.float32))
        / 255
        * 2.5
    )
    np.testing.assert_allclose(result(state, image), expected, atol=2e-7)
    path = tmp_path / "exported.py"
    path.write_text(export_python(state), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("exported_library_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out, _ = module.StudioPipeline(module.STATE).process(image)
    np.testing.assert_array_equal(out["custom"], result(state, image))


@pytest.mark.parametrize(
    "code,match",
    [
        ("def process(c,p):\n    return np.zeros((2,2))", "shape"),
        ('def process(c,p):\n    return c["R"] / 0', "finite"),
        (
            'def process(c,p):\n    raise RuntimeError("deliberate failure")',
            "deliberate failure",
        ),
    ],
)
def test_bad_custom_results_leave_history_unchanged(code, match):
    pipeline = StudioPipeline(state_for("custom", code=code))
    with pytest.raises(ValueError, match=match):
        pipeline.process(demo_frame(0, 20, 20))
    assert pipeline.previous is None


def test_timeout():
    start = time.monotonic()
    with pytest.raises(ValueError, match="exceeded"):
        result(
            state_for(
                "custom", code="def process(c,p):\n    while True: pass", timeout=0.2
            )
        )
    assert time.monotonic() - start < 4


def test_import_and_configuration_never_execute_custom_code(tmp_path):
    marker = tmp_path / "side-effect.txt"
    code = f'def process(c,p):\n    from pathlib import Path\n    Path({str(marker)!r}).write_text("executed")\n    return c["R"]'
    session = StudioSession(tmp_path / "storage", backend="current")
    session.configure(state_for("custom", code=code))
    assert not marker.exists()
    assert session.frame()["needsCodeRun"]
    assert not marker.exists() and session.index == 0
    session.frame(run_code=True)
    assert marker.exists() and session.index == 1
    changed = copy.deepcopy(session.state)
    changed["nodes"][-1]["params"]["gain"] = 2
    session.configure(changed)
    assert session.frame()["needsCodeRun"]


def test_runtime_compatibility():
    with pytest.raises(ValueError, match="compatible"):
        validate_state(state_for("gaussian", "javascript"))
    with pytest.raises(ValueError, match="compatible"):
        validate_state(state_for("custom", "missing-language"))
    assert runtime_catalog()["python"]["available"]
    with pytest.raises(ValueError, match="Canny"):
        validate_state(state_for("canny", low=100, high=50))
    with pytest.raises(ValueError):
        validate_state(state_for("components", minArea=1.2))


def test_examples_and_saved_dependencies(tmp_path):
    catalog = library_catalog(tmp_path)
    examples = [e for e in catalog["entries"] if e["type"] == "example"]
    assert len(examples) >= 5
    for entry in examples:
        values, ready = StudioPipeline(entry["state"]).process(demo_frame(0, 160, 120))
        assert np.isfinite(values[entry["state"]["view"]["result"]]).all()
        if entry["id"] == "example:lines":
            assert np.count_nonzero(values["lines"]) > 100
    assert len([e for e in catalog["entries"] if e["type"] == "reference"]) == 37
    assert any(e["id"] == "api:Canny" for e in catalog["entries"])
    state = default_state()
    saved = save_library_block(
        tmp_path, {"state": state, "selected": "gaussian", "name": "Reusable smooth"}
    )
    entry = next(e for e in saved["entries"] if e["group"] == "savedGroup")
    assert len(entry["state"]["nodes"]) == 5
    assert entry["state"]["view"]["result"] == "smooth"
    assert (
        entry["state"]
        == next(
            e for e in library_catalog(tmp_path)["entries"] if e["id"] == entry["id"]
        )["state"]
    )
    save_library_block(
        tmp_path, {"state": state, "selected": "gaussian", "name": "Reusable smooth"}
    )
    assert len(list((tmp_path / "blocks").glob("*.json"))) == 2
