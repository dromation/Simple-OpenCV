"""Reference external adapter: Python source file, file protocol v1.

This separate adapter demonstrates the public protocol. Other languages need
their own interpreter/compiler wrapper implementing the same file contract.
It deliberately exposes NumPy only, with no automatic OpenCV import.
"""
import json
import sys
from pathlib import Path

import numpy as np

root, source = map(Path, sys.argv[1:3])
try:
    request = json.loads((root / "request.json").read_text(encoding="utf-8"))
    assert request["api"] == 1 and request["dtype"] == "<f4"
    shape = tuple(request["shape"])
    channels = {
        name: np.fromfile(root / f"in{i}.bin", dtype="<f4").reshape(shape)
        for i, name in enumerate(request["channels"])
    }
    scope = {"np": np, "__name__": "user_block"}
    exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), scope)
    output = np.asarray(scope["process"](channels, request["params"]), dtype="<f4")
    if output.shape != shape or not np.isfinite(output).all():
        raise ValueError("Expected one finite H x W output")
    output.tofile(root / "out.bin")
except BaseException as exc:
    (root / "error.txt").write_text(str(exc)[:1800], encoding="utf-8")
    sys.exit(1)
