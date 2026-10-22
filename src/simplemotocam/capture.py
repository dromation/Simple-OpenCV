"""OpenCV acquisition is independent of channel processing and the legacy GUI."""
import cv2


class OpenCVCapture:
    def __init__(self, source: int | str = 0):
        self.source = source
        self._capture = None

    def __enter__(self):
        if self._capture is not None:
            raise RuntimeError("Capture is already open")
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Cannot open video source: {self.source}")
        self._capture = cap
        return self

    def __iter__(self):
        if self._capture is None:
            raise RuntimeError("Use capture inside a with block")
        while True:
            ok, frame = self._capture.read()
            if not ok:
                if isinstance(self.source, int):
                    raise RuntimeError("Camera stopped delivering frames")
                return
            yield frame

    def __exit__(self, *exc):
        if self._capture is not None:
            self._capture.release()
            self._capture = None
