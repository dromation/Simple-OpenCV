"""Validated ordered dataflow for the visual studio; also embedded in exports.

Only NumPy/OpenCV and the standard library are required. Expressions are parsed
as a small mathematical language, never passed to eval or exec.
"""

import ast
import copy
import json
import math
import re
import cv2
import numpy as np
from .studio_runtime import (
    check_runtime,
    run_worker,
    run_javascript_builtin,
    STARTERS,
    language_id,
    run_language_block,
)  # EXPORT_RUNTIME

from .studio_backend import (
    validate_backend,
    CV24_NATIVE,
    CV24_INDEPENDENT,
    run_opencv24,
    run_current,
    legacy_custom_context,
)  # EXPORT_BACKEND

SCHEMA_VERSION = 1
BASE = {"R", "G", "B", "A"}
FUNCTIONS = {
    "abs": (np.abs, 1),
    "sqrt": (np.sqrt, 1),
    "minimum": (np.minimum, 2),
    "maximum": (np.maximum, 2),
    "clip": (np.clip, 3),
}
KINDS = {
    "source": {"label": "Zajem", "lesson": "channels", "params": {}},
    "channels": {"label": "RGB kanali", "lesson": "channels", "params": {}},
    "difference": {"label": "Razlika sličic", "lesson": "difference", "params": {}},
    "algebra": {
        "label": "Algebra kanalov",
        "lesson": "algebra",
        "params": {
            "expression": "wR*dR + wG*dG + wB*dB",
            "wR": 1.0,
            "wG": -1.0,
            "wB": 0.5,
            "output": "S",
        },
    },
    "confidence": {
        "label": "Zanesljivost A",
        "lesson": "confidence",
        "params": {"margin": 0.05, "output": "quality"},
    },
    "gaussian": {
        "label": "Gauss",
        "lesson": "filter",
        "params": {"input": "S", "sigma": 1.2, "size": 5, "output": "smooth"},
    },
    "median": {
        "label": "Mediana",
        "lesson": "filter",
        "params": {"input": "R", "size": 3, "output": "median"},
    },
    "kernel": {
        "label": "Lastno jedro",
        "lesson": "filter",
        "params": {
            "input": "R",
            "kernel": [[0, -1, 0], [-1, 4, -1], [0, -1, 0]],
            "output": "filtered",
        },
    },
    "sobel": {
        "label": "Sobel",
        "lesson": "gradient",
        "params": {"input": "smooth", "size": 3, "output": "edges"},
    },
    "scharr": {
        "label": "Scharr",
        "lesson": "gradient",
        "params": {"input": "R", "output": "scharr"},
    },
    "threshold": {
        "label": "Prag",
        "lesson": "threshold",
        "params": {"input": "edges", "threshold": 0.05, "output": "mask"},
    },
}


# Public catalog of executable blocks; UI derives its library from this registry.
for kind, label, lesson, params in [
    ("luminance", "Sivinska svetlost", "channels", {"output": "gray"}),
    (
        "color_distance",
        "Barvna razdalja",
        "channels",
        {"red": 0.0, "green": 0.0, "blue": 0.0, "output": "distance"},
    ),
    ("invert", "Obrat signala", "algebra", {"input": "R", "output": "inverted"}),
    ("box", "Povprečenje", "filter", {"input": "R", "size": 3, "output": "average"}),
    (
        "bilateral",
        "Bilateralni filter",
        "filter",
        {
            "input": "R",
            "size": 5,
            "sigma": 1.2,
            "colorSigma": 0.1,
            "output": "bilateral",
        },
    ),
    ("laplacian", "Laplace", "gradient", {"input": "R", "output": "laplace"}),
    (
        "canny",
        "Canny",
        "gradient",
        {"input": "R", "low": 50, "high": 100, "output": "canny"},
    ),
    ("otsu", "Otsujev prag", "threshold", {"input": "R", "output": "otsu"}),
    (
        "adaptive",
        "Prilagodljivi prag",
        "threshold",
        {"input": "R", "size": 11, "offset": 2.0, "output": "adaptive"},
    ),
    (
        "components",
        "Povezana območja",
        "threshold",
        {"input": "R", "minArea": 20, "output": "blobs"},
    ),
    (
        "hough",
        "Houghove daljice",
        "gradient",
        {"input": "R", "votes": 30, "minLength": 30, "maxGap": 5, "output": "lines"},
    ),
    (
        "custom",
        "Lastna koda",
        "algebra",
        {"input": "R", "code": "", "gain": 1.0, "timeout": 5.0, "output": "custom"},
    ),
]:
    KINDS[kind] = {"label": label, "lesson": lesson, "params": params}
for kind in ("erode", "dilate", "opening", "closing", "morph_gradient"):
    KINDS[kind] = {
        "label": kind,
        "lesson": "filter",
        "params": {"input": "R", "size": 3, "iterations": 1, "output": kind},
    }
for kind, descriptor in KINDS.items():
    descriptor["category"] = (
        "customGroup"
        if kind == "custom"
        else (
            "mathGroup"
            if descriptor["lesson"]
            in ("channels", "algebra", "difference", "confidence")
            else "filterGroup"
        )
    )


BLOCK_FORMULAS = {
    "luminance": "Y = 0.299 R + 0.587 G + 0.114 B",
    "color_distance": "D = sqrt((R-r)² + (G-g)² + (B-b)²) / sqrt(3)",
    "invert": "O = 1 - I",
    "box": "O(x,y) = sum(I(x+i,y+j)) / size²",
    "bilateral": "O(p) = sum(w(p,q) I(q)) / sum(w(p,q))\nw = exp(-||p-q||²/(2σs²) - (I(p)-I(q))²/(2σc²))",
    "laplacian": "O = I(x-1,y) + I(x+1,y) + I(x,y-1) + I(x,y+1) - 4 I(x,y)",
    "canny": "I8 = round(255 clip(I,0,1))\nCanny(I8, low, high, L2=true) / 255",
    "otsu": "t* = argmax_t [ω0(t) ω1(t) (μ0(t)-μ1(t))²]\nO = 1[I8 > t*]; I8 = round(255 clip(I,0,1))",
    "adaptive": "I8 = round(255 clip(I,0,1))\nO = 1[I8 > GaussianMean(I8, size) - offset]",
    "components": "M = 1[I > 0]; connectivity = 8\nO(p) = 1[p ∈ foreground component C ∧ area(C) ≥ minArea]",
    "hough": "ρ = x cos(θ) + y sin(θ)\nΔρ = 1 px; Δθ = π/180; HoughLinesP(1[I>0])",
    "erode": "O(p) = min_{q ∈ K} I(p+q)",
    "dilate": "O(p) = max_{q ∈ K} I(p+q)",
    "opening": "O = dilate(erode(I,K),K)",
    "closing": "O = erode(dilate(I,K),K)",
    "morph_gradient": "O = dilate(I,K) - erode(I,K)",
}
for kind, formula in BLOCK_FORMULAS.items():
    KINDS[kind]["formula"] = formula


def default_state():
    nodes = []
    for kind in ("source", "channels", "difference", "algebra", "gaussian", "sobel"):
        nodes.append(
            {
                "id": kind,
                "kind": kind,
                "enabled": True,
                "params": copy.deepcopy(KINDS[kind]["params"]),
            }
        )
    return {
        "schema": SCHEMA_VERSION,
        "name": "Change detection",
        "source": {"type": "synthetic", "camera": 0, "asset": ""},
        "nodes": nodes,
        "view": {
            "signal": "S",
            "result": "edges",
            "signed": True,
            "gain": 4.0,
            "locale": "en",
            "codeLanguage": "python",
        },
    }


def number(value, low, high, label, integer=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not low <= value <= high
    ):
        raise ValueError(f"{label}: expected a finite number in [{low}, {high}]")
    if integer and value != int(value):
        raise ValueError(f"{label}: expected an integer")
    return int(value) if integer else float(value)


def expression_tree(text, names):
    if not isinstance(text, str) or len(text) > 500:
        raise ValueError("Expression: maximum 500 characters")
    try:
        tree = ast.parse(text, mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise ValueError("Expression: invalid mathematical syntax") from exc
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise ValueError("Expression is too complex")

    def check(node):
        if isinstance(node, ast.Expression):
            check(node.body)
        elif isinstance(node, ast.Constant):
            number(node.value, -1000000, 1000000, "Constant")
        elif isinstance(node, ast.Name):
            if node.id not in names:
                raise ValueError(f"Unavailable channel or weight: {node.id}")
        elif isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            check(node.operand)
        elif isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
        ):
            if isinstance(node.op, ast.Pow):
                exponent = node.right
                if isinstance(exponent, ast.UnaryOp) and isinstance(
                    exponent.op, (ast.USub, ast.UAdd)
                ):
                    exponent = exponent.operand
                if (
                    not isinstance(exponent, ast.Constant)
                    or not isinstance(exponent.value, (int, float))
                    or isinstance(exponent.value, bool)
                    or not -4 <= exponent.value <= 4
                ):
                    raise ValueError(
                        "Powers require a constant exponent between -4 and 4"
                    )
            check(node.left)
            check(node.right)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS
        ):
            if node.keywords or len(node.args) != FUNCTIONS[node.func.id][1]:
                raise ValueError("Wrong function arguments")
            for arg in node.args:
                check(arg)
        else:
            raise ValueError(
                "Only channel names, numbers, arithmetic and abs/sqrt/minimum/maximum/clip are allowed"
            )

    check(tree)
    return tree


def evaluate(tree, values):
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant):
            return np.float32(node.value)
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.UnaryOp):
            return (
                -visit(node.operand)
                if isinstance(node.op, ast.USub)
                else visit(node.operand)
            )
        if isinstance(node, ast.Call):
            return FUNCTIONS[node.func.id][0](*(visit(a) for a in node.args))
        left, right = visit(node.left), visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return np.divide(left, right)
        return np.power(left, right)

    with np.errstate(all="ignore"):
        return visit(tree)


def validate_state(state):
    if not isinstance(state, dict) or state.get("schema") != SCHEMA_VERSION:
        raise ValueError("Unsupported project schema")
    backend = validate_backend(state.get("backend"))
    name = state.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError("Project name: 1–100 characters")
    source = state.get("source", {})
    if not isinstance(source, dict) or source.get("type") not in (
        "synthetic",
        "camera",
        "image",
        "video",
    ):
        raise ValueError("Invalid source")
    camera = number(source.get("camera", 0), 0, 16, "Camera", True)
    asset = source.get("asset", "")
    if (
        not isinstance(asset, str)
        or len(asset) > 100
        or (asset and not re.fullmatch(r"[a-zA-Z0-9_.-]+", asset))
    ):
        raise ValueError("Invalid source asset")
    if source["type"] in ("image", "video") and not asset:
        raise ValueError("Choose an image or video first")
    nodes = state.get("nodes")
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= 32:
        raise ValueError("Use 2–32 blocks")
    if [n.get("kind") if isinstance(n, dict) else None for n in nodes[:2]] != [
        "source",
        "channels",
    ]:
        raise ValueError("The first two blocks must be source and RGB channels")
    result, names, ids, kinds = [], set(BASE), set(), []
    for n in nodes:
        if not isinstance(n, dict) or n.get("kind") not in KINDS:
            raise ValueError("Unknown block")
        kind, identifier = n["kind"], n.get("id")
        language = n.get("runtime", "python")
        language_id(language)
        if kind != "custom" or n.get("enabled", True):
            check_runtime(language, kind, backend["id"])
        if backend["id"] == "opencv24" and kind not in CV24_NATIVE | CV24_INDEPENDENT:
            raise ValueError(
                f"{kind}: no compatible OpenCV 2.4 adapter; choose the current engine or remove the block"
            )
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,39}", identifier)
            or identifier in ids
        ):
            raise ValueError("Block IDs must be unique")
        ids.add(identifier)
        if kind in ("source", "channels", "difference") and kind in kinds:
            raise ValueError(f"Only one {kind} block is allowed")
        kinds.append(kind)
        enabled = n.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("Enabled must be boolean")
        if "input" not in KINDS[kind]["params"] and not enabled:
            raise ValueError("Only filters and edge estimators support bypass")
        supplied = n.get("params", {})
        if not isinstance(supplied, dict) or set(supplied) - set(KINDS[kind]["params"]):
            raise ValueError("Unknown block parameter")
        p = {**copy.deepcopy(KINDS[kind]["params"]), **supplied}
        if kind == "difference":
            names.update(("dR", "dG", "dB", "dA"))
        if "input" in p and p["input"] not in names:
            raise ValueError(
                f'{kind}: unavailable input {p["input"]}; check block order'
            )
        if kind == "algebra":
            expression_tree(p["expression"], names | {"wR", "wG", "wB"})
            for weight in ("wR", "wG", "wB"):
                p[weight] = number(p[weight], -10, 10, weight)
        if "size" in p:
            allowed = (
                (3, 5)
                if kind == "median"
                else ((3, 5, 7) if kind == "sobel" else (3, 5, 7, 9, 11, 13, 15))
            )
            if isinstance(p["size"], bool) or p["size"] not in allowed:
                raise ValueError(f"{kind}: kernel size must be one of {allowed}")
            p["size"] = int(p["size"])
        if "sigma" in p:
            p["sigma"] = number(p["sigma"], 0.1, 10, "Sigma")
        if "threshold" in p:
            p["threshold"] = number(p["threshold"], -10, 10, "Threshold")
        if "margin" in p:
            p["margin"] = number(p["margin"], 0.001, 0.5, "Confidence margin")
        for key, bounds in {
            "red": (0, 1),
            "green": (0, 1),
            "blue": (0, 1),
            "colorSigma": (0.001, 10),
            "low": (0, 255),
            "high": (0, 255),
            "offset": (-255, 255),
            "minArea": (1, 1000000),
            "votes": (1, 10000),
            "minLength": (1, 10000),
            "maxGap": (0, 10000),
            "iterations": (1, 10),
            "timeout": (0.1, 30),
            "gain": (-100, 100),
        }.items():
            if key in p:
                p[key] = number(
                    p[key],
                    *bounds,
                    key,
                    integer=key
                    in ("minArea", "votes", "minLength", "maxGap", "iterations"),
                )
        if kind == "canny" and p["low"] > p["high"]:
            raise ValueError("Canny: low must not exceed high")
        if kind == "custom":
            if not isinstance(p["code"], str) or len(p["code"]) > 20000:
                raise ValueError("Custom code: maximum 20000 characters")
            if enabled and p["code"].strip() and language == "python":
                try:
                    tree = ast.parse(p["code"])
                except (SyntaxError, RecursionError) as exc:
                    raise ValueError(f"Custom Python syntax: {exc}") from exc
                if not any(
                    isinstance(item, ast.FunctionDef) and item.name == "process"
                    for item in tree.body
                ):
                    raise ValueError("Define process(channels, params)")
        if kind == "kernel":
            try:
                kernel = np.asarray(p["kernel"], dtype=np.float32)
            except (TypeError, ValueError) as exc:
                raise ValueError("Kernel must be a numeric 3×3 matrix") from exc
            if (
                kernel.shape != (3, 3)
                or not np.isfinite(kernel).all()
                or np.abs(kernel).max() > 100
            ):
                raise ValueError("Kernel must be 3×3 with values in [-100,100]")
            p["kernel"] = kernel.tolist()
        if "output" in p:
            output = p["output"]
            if (
                not isinstance(output, str)
                or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,23}", output)
                or output in names | set(FUNCTIONS) | {"wR", "wG", "wB"}
            ):
                raise ValueError("Output name must be a unique channel identifier")
            names.add(output)
        result.append({"id": identifier, "kind": kind, "enabled": enabled, "params": p})
        if language != "python":
            result[-1]["runtime"] = language
        if kind == "custom" and "codeDrafts" in n:
            drafts = n["codeDrafts"]
            if (not isinstance(drafts, dict) or len(drafts) > 32
                or any(not isinstance(code, str) or len(code) > 20000 for code in drafts.values())
                or sum(len(code) for code in drafts.values()) > 120000):
                raise ValueError("Code drafts: up to 32 languages, 20000 characters each, 120000 total")
            for key in drafts:
                language_id(key)
            result[-1]["codeDrafts"] = copy.deepcopy(drafts)
    view = state.get("view", {})
    if not isinstance(view, dict):
        raise ValueError("Invalid view")
    normalized_view = {}
    for key, default in [("signal", "R"), ("result", "R")]:
        value = view.get(key, default)
        if value not in names:
            raise ValueError(f"Preview channel is unavailable: {value}")
        normalized_view[key] = value
    normalized_view["gain"] = number(view.get("gain", 4), 0.1, 100, "Preview gain")
    if not isinstance(view.get("signed", True), bool):
        raise ValueError("Signed display must be boolean")
    normalized_view["signed"] = view.get("signed", True)
    for key, default in [("locale", "en"), ("codeLanguage", "python")]:
        value = view.get(key, default)
        if not isinstance(value, str) or not re.fullmatch("[a-zA-Z-]{1,16}", value):
            raise ValueError("Invalid language")
        normalized_view[key] = value
    return {
        "schema": SCHEMA_VERSION,
        "name": name.strip(),
        "backend": backend,
        "source": {"type": source["type"], "camera": camera, "asset": asset},
        "nodes": result,
        "view": normalized_view,
    }


def normalize_frame(image):
    image = np.asarray(image)
    if image.ndim != 3 or image.shape[2] != 3 or not image.size:
        raise ValueError("Expected a nonempty BGR image")
    if image.dtype == np.uint8:
        rgb = image[..., ::-1].astype(np.float32) / 255
    elif image.dtype == np.uint16:
        rgb = image[..., ::-1].astype(np.float32) / 65535
    elif np.issubdtype(image.dtype, np.floating):
        rgb = image[..., ::-1].astype(np.float32)
    else:
        raise ValueError("Unsupported image type")
    if not np.isfinite(rgb).all() or rgb.min() < 0 or rgb.max() > 1:
        raise ValueError("Floating point images must be normalized to [0,1]")
    return rgb


class StudioPipeline:
    def __init__(self, state):
        self.state = validate_state(state)
        self.previous = None
        self.trees = {
            n["id"]: expression_tree(
                n["params"]["expression"],
                self.available_before(n["id"]) | {"wR", "wG", "wB"},
            )
            for n in self.state["nodes"]
            if n["kind"] == "algebra"
        }

    def available_before(self, identifier):
        names = set(BASE)
        for n in self.state["nodes"]:
            if n["id"] == identifier:
                break
            if n["kind"] == "difference":
                names.update(("dR", "dG", "dB", "dA"))
            if "output" in n["params"]:
                names.add(n["params"]["output"])
        return names

    def process(self, image):
        rgb = normalize_frame(image)
        values = {c: rgb[..., i] for i, c in enumerate("RGB")}
        values["A"] = np.clip(np.minimum(rgb, 1 - rgb).min(axis=2) / 0.05, 0, 1)
        original = {k: v.copy() for k, v in values.items()}
        shape = rgb.shape[:2]
        ready = self.previous is not None and self.previous["R"].shape == shape
        for node in self.state["nodes"]:
            kind, p = node["kind"], node["params"]
            if kind in ("source", "channels"):
                continue
            if kind == "difference":
                values.update(
                    {
                        f"d{c}": (
                            values[c] - self.previous[c]
                            if ready
                            else np.zeros(shape, np.float32)
                        )
                        for c in "RGBA"
                    }
                )
                continue
            if not node["enabled"]:
                output = values[p["input"]].copy()
            elif kind != "custom" and node.get("runtime") in ("c", "cpp", "java"):
                output = run_language_block(node["runtime"], kind, values, p, self.state["backend"]["id"])
            elif (
                self.state["backend"]["id"] == "opencv24"
                and kind in CV24_NATIVE
                and node.get("runtime") != "javascript"
            ):
                output = run_opencv24(kind, values[p["input"]], p)
            elif kind == "custom":
                output = (
                    run_worker(
                        node.get("runtime", "python"),
                        p["code"],
                        values,
                        p,
                        p["timeout"],
                        (
                            legacy_custom_context(KINDS)
                            if self.state["backend"]["id"] == "opencv24"
                            else None
                        ),
                    )
                    if p["code"].strip()
                    else values[p["input"]].copy()
                )
            elif node.get("runtime") == "javascript":
                output = run_javascript_builtin(kind, values, p)
            elif kind == "luminance":
                output = 0.299 * values["R"] + 0.587 * values["G"] + 0.114 * values["B"]
            elif kind == "color_distance":
                output = np.sqrt(
                    sum(
                        (values[c] - p[key]) ** 2
                        for c, key in zip("RGB", ("red", "green", "blue"))
                    )
                ) / np.sqrt(3)
            elif kind == "algebra":
                output = evaluate(
                    self.trees[node["id"]],
                    {**values, **{w: p[w] for w in ("wR", "wG", "wB")}},
                )
            elif kind == "confidence":
                output = np.clip(
                    np.minimum(rgb, 1 - rgb).min(axis=2) / p["margin"], 0, 1
                )
            else:
                output = run_current(kind, values[p["input"]], p)
            output = np.asarray(output, dtype=np.float32)
            if output.ndim == 0:
                output = np.full(shape, output, np.float32)
            if output.shape != shape or not np.isfinite(output).all():
                raise ValueError(
                    f'{node["id"]}: nonfinite result; check division, square roots and magnitudes'
                )
            values[p["output"]] = output
        # A failed operation must never advance the temporal history.
        self.previous = original
        return values, ready


def demo_frame(index, width=640, height=360):
    image = np.full((height, width, 3), 80, np.uint8)
    for x in range(0, width, 40):
        cv2.line(image, (x, 0), (x, height), (88, 88, 88), 1)
    for y in range(0, height, 40):
        cv2.line(image, (0, y), (width, y), (88, 88, 88), 1)
    cx = int(width * 0.5 + math.sin(index * 0.035) * width * 0.22)
    cy = height // 2
    cv2.rectangle(image, (cx - 62, cy - 60), (cx + 62, cy + 60), (45, 45, 210), -1)
    cv2.circle(image, (cx, cy), 40, (145, 145, 145), -1)
    cv2.circle(image, (cx, cy), 28, (30, 30, 30), -1)
    for dx in (-47, 47):
        for dy in (-45, 45):
            cv2.circle(image, (cx + dx, cy + dy), 7, (25, 25, 25), -1)
    return image


def display_plane(plane, signed=False, gain=1):
    # Display mapping only; numerical arrays are never clipped by the pipeline.
    view = 0.5 + plane * gain / 2 if signed else plane * gain
    return np.uint8(np.clip(view, 0, 1) * 255)
