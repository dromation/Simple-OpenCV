import copy
import importlib.util
import json
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import cv2
import numpy as np
import pytest

from simplemotocam.studio_engine import (
    StudioPipeline,
    default_state,
    validate_state,
    demo_frame,
    expression_tree,
)
from simplemotocam.studio import StudioSession, StudioServer, export_python


def test_signed_difference_and_weights():
    state = default_state()
    p = StudioPipeline(state)
    first = np.full((8, 8, 3), 128, np.uint8)
    values, ready = p.process(first)
    assert not ready and not values["S"].any()
    second = first.copy()
    second[..., 2] = 64
    values, ready = p.process(second)
    assert ready
    np.testing.assert_allclose(values["dR"], -64 / 255, atol=1e-7)
    np.testing.assert_allclose(values["S"], values["dR"])
    np.testing.assert_allclose(values["smooth"], values["S"], atol=1e-7)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "R.__class__",
        "R[0]",
        "[x for x in R]",
        "R**100",
        "open(1)",
        "sqrt(R, G)",
        "R; G",
    ],
)
def test_restricted_math(expression):
    with pytest.raises(ValueError):
        expression_tree(expression, {"R", "G"})


def test_history_not_advanced_on_failure():
    state = default_state()
    state["nodes"][3]["params"]["expression"] = "1 / R"
    p = StudioPipeline(state)
    p.process(np.full((8, 8, 3), 128, np.uint8))
    previous = p.previous
    with pytest.raises(ValueError, match="nonfinite"):
        p.process(np.zeros((8, 8, 3), np.uint8))
    assert p.previous is previous


def test_order_validation_and_bypass():
    state = default_state()
    state["nodes"][4], state["nodes"][5] = state["nodes"][5], state["nodes"][4]
    with pytest.raises(ValueError, match="unavailable input"):
        validate_state(state)
    state = default_state()
    state["nodes"][4]["enabled"] = False
    p = StudioPipeline(state)
    p.process(demo_frame(0))
    values, _ = p.process(demo_frame(4))
    np.testing.assert_array_equal(values["smooth"], values["S"])


def test_custom_kernel_and_confidence():
    state = default_state()
    state["nodes"] = state["nodes"][:2] + [
        {
            "id": "k",
            "kind": "kernel",
            "params": {
                "input": "R",
                "output": "filtered",
                "kernel": [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
            },
        },
        {
            "id": "q",
            "kind": "confidence",
            "params": {"margin": 0.1, "output": "quality"},
        },
    ]
    state["view"].update(signal="filtered", result="quality")
    values, _ = StudioPipeline(state).process(np.full((8, 8, 3), 128, np.uint8))
    np.testing.assert_allclose(values["filtered"], 256 / 255)
    assert np.all(values["quality"] == 1)


def test_export_is_standalone_and_matches(tmp_path):
    state = default_state()
    state["nodes"][3]["params"]["wR"] = 2.3
    exported = tmp_path / "algorithm.py"
    exported.write_text(export_python(state), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("exported", exported)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = StudioPipeline(state)
    standalone = module.StudioPipeline(module.STATE)
    for i in range(5):
        expected, _ = original.process(demo_frame(i))
        actual, _ = standalone.process(demo_frame(i))
        for channel in expected:
            np.testing.assert_array_equal(actual[channel], expected[channel])
    result = subprocess.run(
        [sys.executable, str(exported), "--frames", "3"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["frames"] == 3


def test_state_save_and_view_keeps_history(tmp_path):
    s = StudioSession(tmp_path)
    s.frame()
    history = s.pipeline.previous
    state = copy.deepcopy(s.state)
    state["view"]["locale"] = "ja"
    s.configure(state)
    assert s.pipeline.previous is history
    record = s.save(state)
    saved = json.loads(
        (tmp_path / "projects" / f'{record["id"]}.json').read_text(encoding="utf-8")
    )
    assert saved["state"] == validate_state(state)
    assert s.projects()[0]["id"] == record["id"]
    state["nodes"][3]["params"]["wR"] = 2
    s.configure(state)
    assert s.pipeline.previous is None


@pytest.fixture
def server(tmp_path):
    srv = StudioServer(("127.0.0.1", 0), StudioSession(tmp_path))
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()
    thread.join()


def request(server, path, data=None, headers=None):
    url = f"http://127.0.0.1:{server.server_address[1]}{path}"
    payload = None if data is None else json.dumps(data).encode()
    return urllib.request.urlopen(
        urllib.request.Request(url, data=payload, headers=headers or {})
    )


def test_http_session_and_origin(server):
    bootstrap = json.load(request(server, "/api/bootstrap"))
    with pytest.raises(urllib.error.HTTPError) as e:
        request(server, "/api/frame", {})
    assert e.value.code == 403
    headers = {"X-Studio-Token": bootstrap["token"], "Content-Type": "application/json"}
    frame = json.load(request(server, "/api/frame", {}, headers))
    assert frame["frame"] == 1 and frame["images"]["camera"].startswith(
        "data:image/jpeg"
    )
    with pytest.raises(urllib.error.HTTPError) as e:
        request(server, "/api/frame", {}, dict(headers, Origin="https://example.com"))
    assert e.value.code == 403
    with pytest.raises(urllib.error.HTTPError):
        request(server, "/../studio.py")
    record = json.load(request(server, "/api/save", default_state(), headers))
    loaded = json.load(request(server, "/api/projects/" + record["id"]))
    assert loaded["state"] == record["state"]


def test_image_and_video_source(tmp_path):
    session = StudioSession(tmp_path)
    cv2.imwrite(str(tmp_path / "uploads" / "image.png"), demo_frame(0))
    state = default_state()
    state["source"].update(type="image", asset="image.png")
    session.configure(state)
    assert session.frame()["size"] == [640, 360]
    path = tmp_path / "uploads" / "video.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (160, 120))
    assert writer.isOpened()
    for i in range(3):
        writer.write(demo_frame(i, 160, 120))
    writer.release()
    state["source"].update(type="video", asset="video.avi")
    session.configure(state)
    assert all(not session.frame().get("ended") for _ in range(3))
    assert session.frame()["ended"]
    session.close()
