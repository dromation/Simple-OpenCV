import cv2
import numpy as np
import pytest
from simplemotocam.capture import OpenCVCapture
from simplemotocam.cli import main


def test_video_file_capture_and_cli(tmp_path):
    path = tmp_path / "test.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 24))
    assert writer.isOpened()
    for value in (40, 80, 120):
        writer.write(np.full((24, 32, 3), value, np.uint8))
    writer.release()
    capture = OpenCVCapture(str(path))
    with capture:
        frames = list(capture)
    assert len(frames) == 3
    assert frames[2].mean() > frames[0].mean()
    assert capture._capture is None
    assert main(["--video", str(path), "--frames", "10"]) == 0


def test_release_on_processing_failure(monkeypatch):
    class Fake:
        released = False
        def isOpened(self): return True
        def release(self): self.released = True
    fake = Fake()
    monkeypatch.setattr(cv2, "VideoCapture", lambda _: fake)
    with pytest.raises(ValueError):
        with OpenCVCapture(0):
            raise ValueError("processor failed")
    assert fake.released


def test_failed_open_releases_handle(monkeypatch):
    class Fake:
        released = False
        def isOpened(self): return False
        def release(self): self.released = True
    fake = Fake()
    monkeypatch.setattr(cv2, "VideoCapture", lambda _: fake)
    with pytest.raises(RuntimeError, match="Cannot open"):
        with OpenCVCapture(0):
            pass
    assert fake.released
