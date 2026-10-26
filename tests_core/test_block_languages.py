"""Language selection executes real adapters, preserving the chosen CV engine."""
import copy
import importlib.util
import sys

import numpy as np
import pytest

from simplemotocam.studio import export_python
from simplemotocam.studio_backend import CV24_NATIVE, backend_catalog, run_current, run_opencv24
from simplemotocam.studio_compiled import MATH_BLOCKS, compile_block, compile_engine_bridge, compiled_toolchain, run_engine_bridge
from simplemotocam.studio_engine import KINDS, StudioPipeline, default_state, demo_frame
from simplemotocam.studio_runtime import run_language_block, runtime_catalog

LANGUAGES = [pytest.param(language, marks=pytest.mark.skipif(not compiled_toolchain(language), reason=language+" compiler unavailable"))
             for language in ("c", "cpp", "java")]


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("backend", ["opencv24", "current"])
def test_every_vision_block_uses_compiled_bridge_and_exact_engine(language, backend):
    if not backend_catalog()[backend]["available"]:
        pytest.skip("OpenCV 2.4 unavailable")
    plane = np.random.default_rng(5).random((23, 29), dtype=np.float32)
    values = {name: plane.copy() for name in "RGBA"}
    for kind in sorted(CV24_NATIVE):
        params = {**copy.deepcopy(KINDS[kind]["params"]), "input": "R"}
        expected = run_opencv24(kind, plane, params) if backend == "opencv24" else run_current(kind, plane, params)
        before = compile_engine_bridge.cache_info()
        actual = run_language_block(language, kind, values, params, backend)
        after = compile_engine_bridge.cache_info()
        assert after.hits + after.misses == before.hits + before.misses + 1
        np.testing.assert_array_equal(actual, expected, err_msg=language+"/"+backend+"/"+kind)


def math_state(kind, language="python", overrides=None):
    state = default_state()
    params = {**copy.deepcopy(KINDS[kind]["params"]), **(overrides or {})}
    if "input" in params:
        params["input"] = "R"
    if kind == "algebra" and not overrides:
        params["expression"] = "clip(wR*(R-G) + sqrt(abs(B-0.5)), -1, 1)"
    state["nodes"] = state["nodes"][:2] + [{"kind": kind, "id": "math", "runtime": language, "enabled": True, "params": params}]
    state["view"].update(signal=params["output"], result=params["output"])
    return state


@pytest.mark.parametrize("language", LANGUAGES)
def test_all_math_blocks_compile_with_parameter_reuse(language):
    image = np.random.default_rng(5).integers(0, 256, (17, 23, 3), dtype=np.uint8)
    for kind in sorted(MATH_BLOCKS):
        reference, _ = StudioPipeline(math_state(kind)).process(image)
        actual, _ = StudioPipeline(math_state(kind, language)).process(image)
        output = KINDS[kind]["params"]["output"]
        np.testing.assert_allclose(actual[output], reference[output], atol=3e-6, rtol=3e-6, err_msg=kind)
    state = math_state("algebra", language)
    before = compile_block.cache_info()
    state["nodes"][-1]["params"]["wR"] = -2.25
    actual, _ = StudioPipeline(state).process(image)
    assert compile_block.cache_info().misses == before.misses
    state["nodes"][-1]["runtime"] = "python"
    reference, _ = StudioPipeline(state).process(image)
    np.testing.assert_allclose(actual["S"], reference["S"], atol=3e-6)


@pytest.mark.parametrize("language", LANGUAGES)
def test_algebra_nonfinite_is_not_hidden_by_minimum(language):
    state = math_state("algebra", language, {"expression": "minimum(sqrt(-1),1)"})
    pipeline = StudioPipeline(state)
    with pytest.raises(ValueError, match="nonfinite"):
        pipeline.process(demo_frame(0, 12, 10))
    assert pipeline.previous is None


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("backend", ["opencv24", "current"])
def test_mixed_language_graph_exports_and_reloads_exactly(language, backend, tmp_path):
    if not backend_catalog()[backend]["available"]:
        pytest.skip("OpenCV 2.4 unavailable")
    state = default_state()
    state["backend"] = {"id": backend, "version": backend_catalog()[backend]["version"]}
    for node in state["nodes"]:
        if node["kind"] not in ("source", "channels", "difference"):
            node["runtime"] = language
    images = np.random.default_rng(42).integers(0, 256, (2, 24, 32, 3), dtype=np.uint8)
    reference = StudioPipeline(state)
    path = tmp_path / "language_export.py"
    path.write_text(export_python(state), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("language_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    exported = module.StudioPipeline(module.STATE)
    for image in images:
        expected, _ = reference.process(image)
        actual, _ = exported.process(image)
        for channel in expected:
            np.testing.assert_array_equal(actual[channel], expected[channel])
    assert np.any(expected['S'] != 0)


@pytest.mark.parametrize("language", LANGUAGES)
def test_bridge_failure_and_timeout(language, tmp_path):
    arguments = ['a b', 'say "hello"', 'C:\\folder with spaces\\', '', 'back\\"slash']
    root = tmp_path / 'engine folder with spaces'
    root.mkdir()
    import json
    check = 'import sys,json;assert sys.argv[1:]==json.loads(' + repr(json.dumps(arguments)) + ')'
    assert run_engine_bridge(language, [sys.executable, '-c', check, *arguments], root, 5).returncode == 0
    with pytest.raises(ValueError, match="engine failure"):
        run_engine_bridge(language, [sys.executable, "-c", "import sys;sys.stderr.write('engine failure');sys.exit(3)"], tmp_path, 5)
    with pytest.raises(ValueError, match="exceeded"):
        run_engine_bridge(language, [sys.executable, "-c", "import time;time.sleep(30)"], tmp_path, 0.3)


def test_declared_support_matches_implemented_blocks():
    kinds = set(KINDS) - {"source", "channels", "difference"}
    for language in ("c", "cpp", "java"):
        assert set(runtime_catalog()[language]["kinds"]) == kinds
        assert len(kinds) == 25
