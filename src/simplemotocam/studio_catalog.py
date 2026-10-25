"""Library metadata, modern adaptations and user-owned reusable recipes."""

import copy
import json
import secrets
from pathlib import Path
from urllib.parse import quote
import cv2
from .studio_engine import KINDS, default_state, validate_state
from .studio_runtime import runtime_catalog, STARTERS
from .studio_backend import backend_catalog

CATALOG_API = 1


def recipe(identifier, title, specs, source=None):
    state = default_state()
    state["name"] = title
    state["nodes"] = state["nodes"][:2]
    for index, (kind, params) in enumerate(specs):
        state["nodes"].append(
            {
                "id": f"{kind}_{index}",
                "kind": kind,
                "enabled": True,
                "params": {**copy.deepcopy(KINDS[kind]["params"]), **params},
            }
        )
    result = state["nodes"][-1]["params"].get("output", "R")
    state["view"].update(signal=result, result=result, signed=False, gain=1)
    return {
        "id": "example:" + identifier,
        "type": "example",
        "template": True,
        "group": "exampleGroup",
        "label": title,
        "state": validate_state(state),
        "source": source,
        "note": "adaptationHint" if source else "recipeHint",
    }


def library_catalog(storage):
    entries = [
        {
            "id": "block:" + kind,
            "type": "block",
            "kind": kind,
            "group": item["category"],
            "label": item["label"],
        }
        for kind, item in KINDS.items()
        if kind not in ("source", "channels")
    ]
    for name, expression in {
        "abs": "abs(R-G)",
        "sqrt": "sqrt(abs(R-G))",
        "minimum": "minimum(R,G)",
        "maximum": "maximum(R,G)",
        "clip": "clip(R-G,0,1)",
    }.items():
        entries.append(
            {
                "id": "function:" + name,
                "type": "function",
                "group": "functionGroup",
                "label": name,
                "expression": expression,
            }
        )
    vision = "https://github.com/mech-id-x/ComputerVision-MachineVision/blob/2054108d00b46f3ee3070ed733d67a016b1ed918/samples_code/"
    si = "https://github.com/mech-id-x/SI_Eksperimenti_Strojnega_Vida/blob/33ac150c0cf2205313dd91ce3eab511e12c38fe7/"
    entries.extend(
        [
            recipe(
                "color-distance",
                "mech-id-x · color_distance",
                [
                    ("color_distance", {}),
                    ("dilate", {"input": "distance"}),
                    ("threshold", {"input": "dilate", "threshold": 0.4}),
                    ("components", {"input": "mask"}),
                ],
                vision + "color_distance",
            ),
            recipe(
                "blob",
                "mech-id-x · Blob_detect",
                [
                    ("luminance", {}),
                    ("otsu", {"input": "gray"}),
                    ("components", {"input": "otsu", "minArea": 30}),
                ],
                vision + "Blob_detect",
            ),
            recipe(
                "lines",
                "mech-id-x · LinesScan3",
                [
                    ("luminance", {}),
                    ("canny", {"input": "gray", "low": 10, "high": 30}),
                    (
                        "hough",
                        {"input": "canny", "votes": 30, "minLength": 66, "maxGap": 0},
                    ),
                ],
                si + "LinesScan3",
            ),
            recipe(
                "motion",
                "mech-id-x · Test_za_podatke_While_Loop",
                [
                    ("difference", {}),
                    ("algebra", {"expression": "sqrt(dR**2+dG**2+dB**2)"}),
                    ("threshold", {"input": "S", "threshold": 0.08}),
                    ("components", {"input": "mask"}),
                ],
                si + "Test_za_podatke_While_Loop",
            ),
            recipe("contrast", "RGB · R − G", [("algebra", {"expression": "R-G"})]),
        ]
    )
    for repository, base, files in [
        (
            "ComputerVision-MachineVision",
            vision,
            "Blob_detect Blob_Match Blob_normal Camera_sets CamSHIFT color_distance color_distance_2 distance_calculation distance_measurment.py Echo_Server Input_sample Input_test Line_allocation Line_Drawer Line_position Positioning_sample Process_main Simple_run SM_Bollocks_1 SM_Bollocks_2 Whitescreen".split(),
        ),
        (
            "SI_Eksperimenti_Strojnega_Vida",
            si,
            "Blob BlobsMatch BlobstoDetect Diploma_experiments distance_measurment.py Image_select Input_test krneki2 krneki3 LinesScan3 Pozicioniranje Processing SimpleMcam Slike_v_listo SM_Static Test_za_podatke_While_Loop".split(),
        ),
    ]:
        for name in files:
            entries.append(
                {
                    "id": "reference:" + repository + ":" + name,
                    "type": "reference",
                    "group": "referenceGroup",
                    "label": repository + " / " + name,
                    "source": base + quote(name),
                    "note": "legacyHint",
                }
            )
    # Repository presets and the user's saved projects appear alongside reusable blocks.
    presets = Path(__file__).resolve().parents[2] / "contrib/presets"
    for directory, prefix, group in [
        (presets, "preset:", "exampleGroup"),
        (Path(storage) / "projects", "project:", "savedGroup"),
    ]:
        for path in sorted(directory.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                state = validate_state(record.get("state", record))
                entries.append(
                    {
                        "id": prefix + path.stem,
                        "template": prefix == "preset:",
                        "type": "example",
                        "group": group,
                        "label": state["name"],
                        "state": state,
                        "note": "recipeHint",
                    }
                )
            except (ValueError, KeyError, TypeError, OSError):
                continue
    root = Path(storage) / "blocks"
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                saved["state"] = validate_state(saved["state"])
                entries.append(
                    {
                        "id": "saved:" + path.stem,
                        "type": "example",
                        "group": "savedGroup",
                        "label": saved["state"]["name"],
                        "state": saved["state"],
                        "note": "recipeHint",
                    }
                )
            except (ValueError, KeyError, TypeError, OSError):
                # A damaged recipe must not break the executable library.
                continue
    # Inspection catalog only: no arbitrary cv2 attribute is invoked by the server.
    for name in sorted(dir(cv2)):
        if name.startswith("_"):
            continue
        value = getattr(cv2, name)
        if callable(value) or isinstance(value, (int, float, str)):
            entries.append(
                {
                    "id": "api:" + name,
                    "backends": ["current"],
                    "type": "api",
                    "group": "apiGroup",
                    "label": "cv2." + name,
                    "signature": (
                        (getattr(value, "__doc__", "") or "")[:3500]
                        if callable(value)
                        else repr(value)[:300]
                    ),
                    "note": "apiHint",
                }
            )
    for function in (
        "GaussianBlur",
        "medianBlur",
        "blur",
        "bilateralFilter",
        "filter2D",
        "Laplacian",
        "threshold",
        "getDerivKernels",
        "sepFilter2D",
        "Scharr",
        "magnitude",
        "morphologyEx",
        "Canny",
        "adaptiveThreshold",
        "HoughLinesP",
        "line",
    ):
        entries.append(
            {
                "id": "api24:" + function,
                "type": "api",
                "backends": ["opencv24"],
                "group": "apiGroup",
                "label": "cv::" + function,
                "signature": "OpenCV 2.4.13.7 · " + function,
                "source": "https://github.com/opencv/opencv/blob/2.4.13.7/modules/"
                + (
                    "core/include/opencv2/core/core.hpp"
                    if function in ("magnitude", "line")
                    else "imgproc/include/opencv2/imgproc/imgproc.hpp"
                ),
                "note": "legacyCode",
            }
        )
    sequence_file = Path(__file__).with_name("studio_sequences.json")
    if sequence_file.exists():
        for lesson in json.loads(sequence_file.read_text(encoding="utf-8"))["lessons"]:
            entries.append(
                {
                    "id": "sequence:" + lesson["id"],
                    "type": "example",
                    "template": False,
                    "group": "exampleGroup",
                    "label": lesson["title"]["en"],
                    "sequence": lesson["id"],
                    "state": lesson["state"],
                    "note": "recipeHint",
                }
            )
    for entry in entries:
        entry["additional"] = entry["type"] in ("example", "reference")
    return {
        "api": CATALOG_API,
        "opencv": cv2.__version__,
        "backends": backend_catalog(),
        "runtimes": runtime_catalog(),
        "starters": STARTERS,
        "entries": entries,
    }


def save_library_block(storage, data):
    state = validate_state(data["state"])
    selected = data.get("selected")
    index = next((i for i, n in enumerate(state["nodes"]) if n["id"] == selected), None)
    if index is None or index < 2:
        raise ValueError("Select an algorithm to save with its upstream dependencies")
    state["nodes"] = state["nodes"][: index + 1]
    result = state["nodes"][-1]["params"].get("output", "R")
    state["view"].update(signal=result, result=result)
    state["name"] = data.get("name", state["name"])
    state = validate_state(state)
    path = Path(storage) / "blocks"
    path.mkdir(exist_ok=True)
    with (path / (secrets.token_hex(12) + ".json")).open(
        "x", encoding="utf-8"
    ) as handle:
        json.dump(
            {"api": CATALOG_API, "state": state}, handle, ensure_ascii=False, indent=2
        )
    return library_catalog(storage)
