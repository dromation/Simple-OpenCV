"""Compile and run real C/C++/Java blocks, including exported algorithms."""
import importlib.util
import sys

import numpy as np
import pytest

from simplemotocam.studio import StudioSession, export_python
from simplemotocam.studio_backend import backend_catalog
from simplemotocam.studio_compiled import COMPILED_STARTERS, compile_block, compiled_toolchain
from simplemotocam.studio_engine import KINDS, StudioPipeline, default_state, demo_frame
from simplemotocam.studio_runtime import run_worker, runtime_catalog

LANGUAGES = [pytest.param(lang, marks=pytest.mark.skipif(not compiled_toolchain(lang), reason=lang + " compiler missing"))
             for lang in ("c", "cpp", "java")]


def state_for(language, code, backend="current"):
    state = default_state()
    state["backend"] = {"id": backend, "version": backend_catalog()[backend]["version"]}
    state["nodes"] = state["nodes"][:2] + [
        {"id": "difference", "kind": "algebra", "enabled": True,
         "params": {**KINDS["algebra"]["params"], "expression": "R-G", "output": "delta"}},
        {"id": "native", "kind": "custom", "runtime": language, "enabled": True,
         "params": {**KINDS["custom"]["params"], "code": code, "input": "delta", "gain": 1.75}},
        {"id": "blur", "kind": "gaussian", "enabled": True,
         "params": {**KINDS["gaussian"]["params"], "input": "custom"}},
    ]
    state["view"].update(signal="custom", result="smooth")
    return state


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("backend", ["current", "opencv24"])
def test_numerics_cache_and_export(language, backend, tmp_path):
    if not backend_catalog()[backend]["available"]:
        pytest.skip("Native OpenCV 2.4 not installed")
    state = state_for(language, COMPILED_STARTERS[language], backend)
    image = demo_frame(2, 24, 19)
    values, _ = StudioPipeline(state).process(image)
    np.testing.assert_allclose(values["custom"], (values["R"]-values["G"])*1.75, atol=2e-7)
    # New dimensions/gain are runtime data and must not trigger a rebuild.
    before = compile_block.cache_info()
    state["nodes"][3]["params"]["gain"] = -0.5
    second, _ = StudioPipeline(state).process(demo_frame(3, 31, 17))
    np.testing.assert_allclose(second["custom"], (second["R"]-second["G"])*-0.5, atol=1e-7)
    assert compile_block.cache_info().misses == before.misses
    assert compile_block.cache_info().hits > before.hits
    path = tmp_path / "compiled_export.py"
    path.write_text(export_python(state), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("compiled_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    exported, _ = module.StudioPipeline(module.STATE).process(demo_frame(3, 31, 17))
    np.testing.assert_array_equal(exported["custom"], second["custom"])
    np.testing.assert_array_equal(exported["smooth"], second["smooth"])


@pytest.mark.parametrize("language", LANGUAGES)
def test_configuration_does_not_compile_or_execute(language, tmp_path):
    code = COMPILED_STARTERS[language] + "\nintentionally broken code"
    session = StudioSession(tmp_path, backend="current")
    before = compile_block.cache_info()
    session.configure(state_for(language, code))
    assert compile_block.cache_info() == before
    assert session.frame()["needsCodeRun"]
    with pytest.raises(ValueError, match="compilation"):
        session.frame(run_code=True)
    assert session.index == 0 and session.pipeline.previous is None


@pytest.mark.parametrize("language", LANGUAGES)
def test_nonfinite_timeout_and_process_failure(language):
    starter = COMPILED_STARTERS[language]
    code = starter.replace('input[i] * (float)ctx->gain', 'NAN').replace('input[i] * static_cast<float>(ctx.gain)', 'NAN').replace('input[i] * (float)p.gain', 'Float.NaN')
    values = {name: np.ones((3, 4), np.float32) for name in "RGBA"}
    params = {"input": "R", "gain": 1}
    with pytest.raises(ValueError, match="nonfinite"):
        run_worker(language, code, values, params)
    if language == "c":
        loop = 'void process(const SmContext *ctx,float*out){volatile int flag=1;while(flag){}}'
        failure = 'void process(const SmContext *ctx,float*out){exit(7);}'
    elif language == "cpp":
        loop = 'void process(const SmContext& ctx,float*out){volatile int flag=1;while(flag){}}'
        failure = 'void process(const SmContext& ctx,float*out){throw std::runtime_error("deliberate failure");}'
    else:
        loop = 'public static float[] process(Map<String,float[]> c,Params p){while(true){}}'
        failure = 'public static float[] process(Map<String,float[]> c,Params p){throw new RuntimeException("deliberate failure");}'
    with pytest.raises(ValueError, match="exceeded"):
        run_worker(language, loop, values, params, timeout=0.2)
    with pytest.raises(ValueError, match="worker exit 7|deliberate failure"):
        run_worker(language, failure, values, params)


def test_missing_compilers_remain_editable_but_not_executable(monkeypatch):
    import simplemotocam.studio_runtime as runtime
    monkeypatch.setattr(runtime, "compiled_toolchain", lambda language: None)
    for language in ("c", "cpp", "java"):
        assert not runtime_catalog()[language]["available"]
        with pytest.raises(ValueError, match="compatible"):
            runtime.check_runtime(language, "custom")


def test_compiled_protected_translation_signatures():
    import json
    from simplemotocam.studio import UI
    catalogs = json.loads((UI / "i18n.js").read_text(encoding="utf-8").split("window.STUDIO_I18N = ", 1)[1].rstrip(";\n"))
    for item in catalogs.values():
        for key, phrase in [("cCodeContract", "void process(const SmContext *ctx, float *out)"),
                            ("cppCodeContract", "void process(const SmContext& ctx, float *out)"),
                            ("javaCodeContract", "public static float[] process(Map<String, float[]> channels, Params p)")]:
            assert phrase in item["strings"][key]


def test_toolchain_discovery_is_cached_and_path_changes_invalidate_it(monkeypatch):
    import simplemotocam.studio_compiled as compiled
    calls = []
    def which(name, path=None):
        calls.append((name, path))
        return "/compiler/" + name
    compiled._discover_toolchain.cache_clear()
    try:
        monkeypatch.setattr(compiled.shutil, "which", which)
        monkeypatch.setenv("PATH", "first-path")
        assert compiled.compiled_toolchain("java")[:2] == ("/compiler/javac", "/compiler/java")
        compiled.compiled_toolchain("java")
        assert len(calls) == 2
        monkeypatch.setenv("PATH", "second-path")
        compiled.compiled_toolchain("java")
        assert len(calls) == 4
    finally:
        compiled._discover_toolchain.cache_clear()
