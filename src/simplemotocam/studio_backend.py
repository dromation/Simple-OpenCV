"""Explicit OpenCV engine profiles. Never substitute another version silently."""

import functools
import json
import os
import sys
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
    "components",
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
    "custom",
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
        protocol = subprocess.run(
            [path, "--protocol"],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return (
            result.stdout.strip()
            if result.returncode == 0 and protocol.stdout.strip() == "2"
            else ""
        )
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
            "customCode": True,
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
            "OpenCV 2.4.13.7 worker is missing or outdated; run tools/build_opencv24.py"
        )
    version = value.get("version", installed["version"])
    if version != installed["version"]:
        raise ValueError(
            f"Saved OpenCV {version} differs from installed {installed['version']}; explicitly choose the installed engine"
        )
    return {"id": installed["id"], "version": installed["version"]}


def run_opencv24(kind, plane, params, launcher=None):
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
            result = launcher([str(opencv24_worker()), "request.yml"], root, 10) if launcher else subprocess.run(
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


def run_current_worker(kind, plane, params, launcher):
    """Current-engine service called through a compiled language adapter."""
    plane = np.asarray(plane, dtype=np.float32)
    source = globals().get("OPENCV24_CUSTOM_SOURCE") or Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="simplemotocam-current-") as folder:
        root = Path(folder)
        plane.astype("<f4").tofile(root / "input.bin")
        (root / "request.json").write_text(json.dumps({"kind": kind, "shape": plane.shape, "params": params}), encoding="utf-8")
        (root / "backend.py").write_text(source, encoding="utf-8")
        worker = root / "worker.py"
        worker.write_text('''import json, sys
from pathlib import Path
import numpy as np
root=Path(sys.argv[1])
try:
    scope={"__file__":str(root/"backend.py")}
    exec((root/"backend.py").read_text(encoding="utf-8"),scope)
    request=json.loads((root/"request.json").read_text(encoding="utf-8"))
    plane=np.fromfile(root/"input.bin",dtype="<f4").reshape(request["shape"])
    scope["run_current"](request["kind"],plane,request["params"]).astype("<f4").tofile(root/"out.bin")
except BaseException as exc:
    (root/"error.txt").write_text(str(exc)[:3000],encoding="utf-8")
    sys.exit(1)
''', encoding="utf-8")
        result = launcher([sys.executable, "-I", str(worker), str(root)], root, 10)
        error = root / "error.txt"
        if result.returncode:
            raise ValueError("Current OpenCV: " + (error.read_text(encoding="utf-8")[:3000] if error.exists() else str(result.returncode)))
        output = root / "out.bin"
        if not output.is_file() or output.stat().st_size != plane.size * 4:
            raise ValueError("Current OpenCV returned an invalid output size")
        value = np.fromfile(output, dtype="<f4").reshape(plane.shape)
        if not np.isfinite(value).all():
            raise ValueError("Current OpenCV returned nonfinite values")
        return value


def legacy_custom_context(kinds):
    # Exports contain this exact source constant, so user code remains portable.
    source = globals().get("OPENCV24_CUSTOM_SOURCE") or Path(__file__).read_text(
        encoding="utf-8"
    )
    source = (
        "import os\nos.environ['SIMPLEMOTOCAM_OPENCV24_WORKER'] = "
        + repr(str(opencv24_worker()))
        + "\n"
        + source
    )
    return {
        "source": source,
        "defaults": {
            kind: {
                key: value
                for key, value in kinds[kind]["params"].items()
                if key not in ("input", "output")
            }
            for kind in sorted(CV24_NATIVE)
        },
    }


def run_current(kind, plane, p):
    """One exact current-OpenCV implementation shared by all language adapters."""
    if kind not in CV24_NATIVE | {"invert"}:
        raise ValueError("Unknown current OpenCV operation: " + kind)
    if kind == "gaussian":
        output = cv2.GaussianBlur(
            plane,
            (p["size"], p["size"]),
            p["sigma"],
            borderType=cv2.BORDER_REFLECT_101,
        )
    elif kind == "median":
        output = cv2.medianBlur(plane, p["size"])
    elif kind == "kernel":
        output = cv2.filter2D(
            plane,
            -1,
            np.asarray(p["kernel"], np.float32),
            borderType=cv2.BORDER_REFLECT_101,
        )
    elif kind == "invert":
        output = 1 - plane
    elif kind == "box":
        output = cv2.blur(plane, (p["size"], p["size"]))
    elif kind == "bilateral":
        output = cv2.bilateralFilter(
            plane, p["size"], p["colorSigma"], p["sigma"]
        )
    elif kind == "laplacian":
        output = cv2.Laplacian(plane, cv2.CV_32F, ksize=1)
    elif kind in (
        "erode",
        "dilate",
        "opening",
        "closing",
        "morph_gradient",
    ):
        operation = {
            "erode": cv2.MORPH_ERODE,
            "dilate": cv2.MORPH_DILATE,
            "opening": cv2.MORPH_OPEN,
            "closing": cv2.MORPH_CLOSE,
            "morph_gradient": cv2.MORPH_GRADIENT,
        }[kind]
        output = cv2.morphologyEx(
            plane,
            operation,
            np.ones((p["size"], p["size"]), np.uint8),
            iterations=p["iterations"],
        )
    elif kind in ("canny", "otsu", "adaptive"):
        # Explicit 8-bit intensity contract, independent of display gain.
        byte = np.rint(np.clip(plane, 0, 1) * 255).astype(np.uint8)
        if kind == "canny":
            output = (
                cv2.Canny(byte, p["low"], p["high"], L2gradient=True)
                / 255.0
            )
        elif kind == "otsu":
            output = (
                cv2.threshold(
                    byte, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
                )[1]
                / 255.0
            )
        else:
            output = (
                cv2.adaptiveThreshold(
                    byte,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    p["size"],
                    p["offset"],
                )
                / 255.0
            )
    elif kind == "components":
        count, labels, stats, centers = cv2.connectedComponentsWithStats(
            (plane > 0).astype(np.uint8), connectivity=8
        )
        keep = stats[:, cv2.CC_STAT_AREA] >= p["minArea"]
        keep[0] = False
        output = keep[labels].astype(np.float32)
    elif kind == "hough":
        lines = cv2.HoughLinesP(
            (plane > 0).astype(np.uint8) * 255,
            1,
            np.pi / 180,
            p["votes"],
            minLineLength=p["minLength"],
            maxLineGap=p["maxGap"],
        )
        output = np.zeros(plane.shape, np.float32)
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                cv2.line(
                    output, (int(x1), int(y1)), (int(x2), int(y2)), 1, 1
                )
    elif kind == "threshold":
        output = (plane > p["threshold"]).astype(np.float32)
    else:
        ksize = p.get("size", 3)
        if kind == "scharr":
            dx = cv2.Scharr(plane, cv2.CV_32F, 1, 0, scale=1 / 32)
            dy = cv2.Scharr(plane, cv2.CV_32F, 0, 1, scale=1 / 32)
        else:
            # Normalise each Sobel derivative to response 1 on a unit ramp.
            kx, ky = cv2.getDerivKernels(1, 0, ksize, normalize=True)
            dx = cv2.sepFilter2D(plane, -1, kx, ky)
            kx, ky = cv2.getDerivKernels(0, 1, ksize, normalize=True)
            dy = cv2.sepFilter2D(plane, -1, kx, ky)
        output = np.hypot(dx, dy)
    return np.asarray(output, dtype=np.float32)
