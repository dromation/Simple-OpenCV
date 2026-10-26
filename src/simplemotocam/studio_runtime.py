"""Versioned local worker adapters. User code has local-user permissions, not a sandbox.

Contract v1: float32 H×W channels -> one finite H×W channel. Adding an adapter
requires validation, availability, execution and numerical contract tests.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
from .studio_compiled import COMPILED_STARTERS, MATH_BLOCKS, compiled_toolchain, run_compiled, run_math_block, run_engine_bridge  # EXPORT_COMPILED
from .studio_backend import CV24_NATIVE, run_opencv24, run_current_worker  # EXPORT_VISION

RUNTIME_API = 1
RUNTIME_REGISTRY = {
    "python": {"name": "Python · NumPy / OpenCV", "kinds": "*"},
    "javascript": {
        "name": "JavaScript · Node.js",
        "kinds": ["custom", "invert", "luminance", "threshold", "color_distance"],
    },
    "cpp": {"name": "C++ · C++17", "kinds": sorted({"custom"} | MATH_BLOCKS | CV24_NATIVE), "reason": "compilerMissing"},
    "java": {"name": "Java · JDK", "kinds": sorted({"custom"} | MATH_BLOCKS | CV24_NATIVE), "reason": "compilerMissing"},
    "c": {"name": "C · C11", "kinds": sorted({"custom"} | MATH_BLOCKS | CV24_NATIVE), "reason": "compilerMissing"},
}
STARTERS = {
    **COMPILED_STARTERS,
    "python": 'def process(channels, params):\n    return channels[params["input"]].copy()\n',
    "javascript": "function process(channels, params, shape) {\n  return new Float32Array(channels[params.input]);\n}\n",
}


def language_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_+.#-]{0,39}", value):
        raise ValueError("Language ID: use 1–40 lowercase letters, digits or _ + . # -")
    return value


def external_adapters():
    """Read trusted local configuration, never commands embedded in a project."""
    location = os.environ.get("SIMPLEMOTOCAM_RUNTIME_CONFIG")
    if not location:
        return {}
    document = json.loads(Path(location).read_text(encoding="utf-8"))
    if document.get("api") != RUNTIME_API or not isinstance(document.get("adapters"), dict):
        raise ValueError("Runtime configuration requires api: 1 and adapters")
    result = {}
    for key, item in document["adapters"].items():
        language_id(key)
        if key in ("python", "javascript") or not isinstance(item, dict):
            raise ValueError("External adapters cannot replace built-in Python/JavaScript")
        command = item.get("command")
        extension = item.get("extension", ".txt")
        backends = item.get("backends", ["opencv24", "current"])
        name = item.get("name", key)
        if (not isinstance(command, list) or not command
            or any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in command)
            or not isinstance(extension, str) or not re.fullmatch(r"\.[a-zA-Z0-9]{1,12}", extension)
            or not isinstance(backends, list) or not backends
            or any(b not in ("opencv24", "current") for b in backends)
            or not isinstance(name, str) or not 1 <= len(name) <= 100):
            raise ValueError("Invalid external adapter: " + key)
        result[key] = {"name": name, "command": command, "extension": extension,
                       "backends": backends, "kinds": ["custom"],
                       "available": shutil.which(command[0]) is not None, "api": RUNTIME_API}
    return result


def runtime_catalog():
    entries = {
        key: {
            **item,
            "available": key == "python"
            or (key == "javascript" and shutil.which("node") is not None)
            or (key in COMPILED_STARTERS and compiled_toolchain(key) is not None),
            "api": RUNTIME_API,
        }
        for key, item in RUNTIME_REGISTRY.items()
    }
    for key in COMPILED_STARTERS:
        entries[key]["execution"] = {"compiledMath": sorted(MATH_BLOCKS), "sharedOpenCV": sorted(CV24_NATIVE)}
    for key, item in external_adapters().items():
        entries[key] = {k: v for k, v in item.items() if k not in ("command", "extension")}
    return entries


def check_runtime(language, kind, backend=None):
    language_id(language)
    entry = runtime_catalog().get(language)
    if (
        not entry
        or not entry["available"]
        or (entry["kinds"] != "*" and kind not in entry["kinds"])
        or (backend and backend not in entry.get("backends", ["opencv24", "current"]))
    ):
        raise ValueError(f"{language}: no compatible installed adapter for {kind}")


def run_language_block(language, kind, values, params, backend):
    check_runtime(language, kind, backend)
    if kind in MATH_BLOCKS:
        return run_math_block(language, kind, values, params, backend)
    launcher = lambda command, root, timeout: run_engine_bridge(language, command, root, timeout)
    if backend == "opencv24":
        return run_opencv24(kind, values[params["input"]], params, launcher)
    return run_current_worker(kind, values[params["input"]], params, launcher)


PYTHON_WORKER = r"""import json, sys
from pathlib import Path
import numpy as np
root=Path(sys.argv[1])
try:
    request=json.loads((root/"request.json").read_text(encoding="utf-8"))
    shape=tuple(request["shape"])
    channels={name:np.fromfile(root/f"in{i}.bin",dtype="<f4").reshape(shape) for i,name in enumerate(request["channels"])}
    if request.get("backend") == "opencv24":
        import types
        native={"__file__":str(root/"legacy_backend.py")}
        exec((root/"legacy_backend.py").read_text(encoding="utf-8"),native)
        def operation(kind, plane, **params):
            if kind not in request["nativeDefaults"]:
                raise ValueError("Unknown native OpenCV 2.4 operation: " + str(kind))
            value=np.asarray(plane,dtype=np.float32)
            if value.shape != shape or not np.isfinite(value).all():
                raise ValueError("cv24.run requires a finite H x W plane")
            defaults=request["nativeDefaults"][kind]
            if set(params)-set(defaults):
                raise ValueError("Unknown parameters: " + str(sorted(set(params)-set(defaults))))
            return native["run_opencv24"](kind,value,{**defaults,**params})
        cv24=types.ModuleType("cv24")
        cv24.__version__="2.4.13.7"
        cv24.run=operation
        # Do not let normal `import cv2` silently select the host's OpenCV 4.
        def unsupported(name):
            raise AttributeError("This OpenCV 2.4 bridge exposes cv24.run(kind, plane, **params); it is not the full legacy cv2 Python binding: " + name)
        cv24.__getattr__=unsupported
        sys.modules["cv24"]=cv24
        sys.modules["cv2"]=cv24
        scope={"np":np,"cv24":cv24,"cv2":cv24,"__name__":"simplemotocam_user_block"}
    else:
        import cv2
        scope={"np":np,"cv2":cv2,"__name__":"simplemotocam_user_block"}
    exec(compile(request["code"],"<custom-block>","exec"),scope)
    output=np.asarray(scope["process"](channels,request["params"]),dtype=np.float32)
    if output.shape!=shape or not np.isfinite(output).all():
        raise ValueError("Return one finite H x W array with the same shape as the input")
    output.astype("<f4").tofile(root/"out.bin")
except BaseException as exc:
    (root/"error.txt").write_text(f"{type(exc).__name__}: {str(exc)[:1800]}",encoding="utf-8")
    sys.exit(1)
"""
JS_WORKER = r"""const fs=require("fs"),path=require("path"),root=process.argv[2];
try {
 const q=JSON.parse(fs.readFileSync(path.join(root,"request.json"),"utf8"));
 const channels={};
 q.channels.forEach((name,i)=>{const b=fs.readFileSync(path.join(root,`in${i}.bin`)); channels[name]=new Float32Array(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));});
 const fn=new Function(q.code+"\nreturn process;")();
 const result=fn(channels,q.params,q.shape);
 if (!(Array.isArray(result)||result instanceof Float32Array||result instanceof Float64Array)||result.length!==q.shape[0]*q.shape[1]) throw Error("Return a flat array of H * W values");
 const output=Float32Array.from(result);
 if (!output.every(Number.isFinite)) throw Error("Return finite float32 values");
 fs.writeFileSync(path.join(root,"out.bin"),Buffer.from(output.buffer));
} catch(e) {fs.writeFileSync(path.join(root,"error.txt"),String(e).slice(0,1800));process.exit(1);}
"""


def run_worker(language, code, values, params, timeout=5, legacy=None):
    check_runtime(language, "custom", "opencv24" if legacy else "current")
    if language in COMPILED_STARTERS and language not in external_adapters():
        return run_compiled(language, code, values, params, timeout, "opencv24" if legacy else "current")
    shape = values["R"].shape
    with tempfile.TemporaryDirectory(prefix="simplemotocam-worker-") as folder:
        root = Path(folder)
        if legacy:
            (root / "legacy_backend.py").write_text(legacy["source"], encoding="utf-8")
        for i, plane in enumerate(values.values()):
            np.asarray(plane, dtype="<f4").tofile(root / f"in{i}.bin")
        (root / "request.json").write_text(
            json.dumps(
                {
                    "shape": shape,
                    "channels": list(values),
                    "params": params,
                    "code": code,
                    "api": RUNTIME_API,
                    "language": language,
                    "dtype": "<f4",
                    "backend": "opencv24" if legacy else "current",
                    "nativeDefaults": legacy["defaults"] if legacy else {},
                }
            ),
            encoding="utf-8",
        )
        if language in ("python", "javascript"):
            runner = root / ("worker.py" if language == "python" else "worker.cjs")
            runner.write_text(PYTHON_WORKER if language == "python" else JS_WORKER, encoding="utf-8")
            command = ([sys.executable, "-I", str(runner), str(root)] if language == "python"
                       else [shutil.which("node"), "--max-old-space-size=256", str(runner), str(root)])
        else:
            adapter = external_adapters()[language]
            source = root / ("source" + adapter["extension"])
            source.write_text(code, encoding="utf-8")
            # Positional arguments appended without a shell: work directory, source file.
            command = [*adapter["command"], str(root), str(source)]
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(f"Custom block exceeded {timeout:g} s") from exc
        error = root / "error.txt"
        if completed.returncode or error.exists():
            detail = f"worker exit {completed.returncode}"
            if error.exists():
                with error.open(encoding="utf-8") as handle:
                    detail = handle.read(2000)
            raise ValueError("Custom block: " + detail)
        output = root / "out.bin"
        if not output.exists() or output.stat().st_size != int(np.prod(shape)) * 4:
            raise ValueError("Custom block returned an invalid output size")
        result = np.fromfile(output, dtype="<f4").reshape(shape)
        if not np.isfinite(result).all():
            raise ValueError("Custom block returned nonfinite values")
        return result


def run_javascript_builtin(kind, values, params):
    expressions = {
        "invert": "1-channels[params.input][i]",
        "luminance": "0.299*channels.R[i]+0.587*channels.G[i]+0.114*channels.B[i]",
        "threshold": "channels[params.input][i]>params.threshold?1:0",
        "color_distance": "Math.sqrt((channels.R[i]-params.red)**2+(channels.G[i]-params.green)**2+(channels.B[i]-params.blue)**2)/Math.sqrt(3)",
    }
    code = (
        "function process(channels,params,shape){const out=new Float32Array(shape[0]*shape[1]);for(let i=0;i<out.length;i++){out[i]="
        + expressions[kind]
        + ";}return out;}"
    )
    return run_worker("javascript", code, values, params)
