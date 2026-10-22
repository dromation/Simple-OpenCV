"""Explicit OpenCV engine profiles. Never substitute another version silently."""

import functools
import os
from pathlib import Path
import subprocess
import tempfile
import cv2
import numpy as np

CV24_NATIVE = {
    "gaussian",
    "median",
    "kernel",
    "sobel",
    "scharr",
    "threshold",
    "box",
    "bilateral",
    "laplacian",
    "canny",
    "otsu",
    "adaptive",
    "hough",
    "erode",
    "dilate",
    "opening",
    "closing",
    "morph_gradient",
}
CV24_INDEPENDENT = {
    "source",
    "channels",
    "difference",
    "algebra",
    "confidence",
    "luminance",
    "color_distance",
    "invert",
}


def opencv24_worker():
    override = os.environ.get("SIMPLEMOTOCAM_OPENCV24_WORKER")
    if override:
        return Path(override).expanduser().resolve()
    filename = (
        "simplemotocam_opencv24.exe" if os.name == "nt" else "simplemotocam_opencv24"
    )
    local = Path(__file__).resolve()
    project = local.parents[min(2, len(local.parents) - 1)]
    candidates = [
        local.parent / "opencv24" / filename,
        project / ".motocam/backends/opencv24" / filename,
    ]
    hint = globals().get("OPENCV24_EXPORT_HINT")
    if hint:
        candidates.append(Path(hint))
    return next((path for path in candidates if path.is_file()), candidates[1])


@functools.lru_cache(maxsize=8)
def probe_worker(path, modified, size):
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def backend_catalog():
    worker = opencv24_worker()
    version = ""
    try:
        stat = worker.stat()
        version = probe_worker(str(worker), stat.st_mtime_ns, stat.st_size)
    except OSError:
        pass
    return {
        "opencv24": {
            "id": "opencv24",
            "version": "2.4.13.7",
            "available": version == "2.4.13.7",
            "kinds": sorted(CV24_NATIVE | CV24_INDEPENDENT),
            "customCode": False,
        },
        "current": {
            "id": "current",
            "version": cv2.__version__,
            "available": True,
            "kinds": "*",
            "customCode": True,
        },
    }


def validate_backend(value):
    if value is None:
        value = {"id": "current", "version": cv2.__version__}
    if not isinstance(value, dict) or value.get("id") not in ("opencv24", "current"):
        raise ValueError("Unknown OpenCV engine profile")
    installed = backend_catalog()[value["id"]]
    if not installed["available"]:
        raise ValueError(
            "OpenCV 2.4.13.7 worker is not installed; run tools/build_opencv24.py"
        )
    version = value.get("version", installed["version"])
    if version != installed["version"]:
        raise ValueError(
            f"Saved OpenCV {version} differs from installed {installed['version']}; explicitly choose the installed engine"
        )
    return {"id": installed["id"], "version": installed["version"]}


def run_opencv24(kind, plane, params):
    if kind not in CV24_NATIVE:
        raise ValueError("No OpenCV 2.4 adapter for " + kind)
    profile = backend_catalog()["opencv24"]
    if not profile["available"]:
        raise ValueError("OpenCV 2.4 worker is unavailable")
    plane = np.asarray(plane, dtype=np.float32)
    with tempfile.TemporaryDirectory(prefix="simplemotocam-cv24-") as folder:
        root = Path(folder)
        plane.astype("<f4").tofile(root / "input.bin")
        if kind in ("canny", "otsu", "adaptive"):
            np.rint(np.clip(plane, 0, 1) * 255).astype(np.uint8).tofile(
                root / "byte.bin"
            )
        lines = [
            "%YAML:1.0",
            f"kind: {kind}",
            f"rows: {plane.shape[0]}",
            f"cols: {plane.shape[1]}",
        ]
        for key, value in params.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                lines.append(f"{key}: {value}")
        if kind == "kernel":
            flat = np.asarray(params["kernel"], dtype=np.float32).ravel()
            lines += [
                "kernel: !!opencv-matrix",
                "   rows: 3",
                "   cols: 3",
                "   dt: f",
                "   data: [ " + ", ".join(str(float(v)) for v in flat) + " ]",
            ]
        (root / "request.yml").write_text("\n".join(lines) + "\n", encoding="ascii")
        try:
            result = subprocess.run(
                [str(opencv24_worker()), "request.yml"],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError("OpenCV 2.4 operation exceeded 10 seconds") from exc
        if result.returncode:
            error = root / "error.txt"
            with (
                error.open(encoding="utf-8", errors="replace")
                if error.exists()
                else open(os.devnull)
            ) as handle:
                detail = handle.read(2000)
            raise ValueError(
                "OpenCV 2.4: " + (detail or f"worker exit {result.returncode}")
            )
        output = root / "out.bin"
        if not output.is_file() or output.stat().st_size != plane.size * 4:
            raise ValueError("OpenCV 2.4 returned an invalid shape")
        value = np.fromfile(output, dtype="<f4").reshape(plane.shape)
        if not np.isfinite(value).all():
            raise ValueError("OpenCV 2.4 returned nonfinite values")
        return value
