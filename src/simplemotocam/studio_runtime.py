"""Versioned local worker adapters. User code has local-user permissions, not a sandbox.

Contract v1: float32 H×W channels -> one finite H×W channel. Adding an adapter
requires validation, availability, execution and numerical contract tests.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np

RUNTIME_API = 1
RUNTIME_REGISTRY = {
    "python": {"name": "Python · NumPy / OpenCV", "kinds": "*"},
    "javascript": {
        "name": "JavaScript · Node.js",
        "kinds": ["custom", "invert", "luminance", "threshold", "color_distance"],
    },
    "cpp": {"name": "C++", "kinds": [], "reason": "adapterMissing"},
    "java": {"name": "Java", "kinds": [], "reason": "adapterMissing"},
    "c": {"name": "C", "kinds": [], "reason": "adapterMissing"},
}
STARTERS = {
    "python": 'def process(channels, params):\n    return channels[params["input"]].copy()\n',
    "javascript": "function process(channels, params, shape) {\n  return new Float32Array(channels[params.input]);\n}\n",
}


def runtime_catalog():
    return {
        key: {
            **item,
            "available": key == "python"
            or (key == "javascript" and shutil.which("node") is not None),
            "api": RUNTIME_API,
        }
        for key, item in RUNTIME_REGISTRY.items()
    }


def check_runtime(language, kind):
    entry = runtime_catalog().get(language)
    if (
        not entry
        or not entry["available"]
        or (entry["kinds"] != "*" and kind not in entry["kinds"])
    ):
        raise ValueError(f"{language}: no compatible installed adapter for {kind}")


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
    check_runtime(language, "custom")
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
                    "backend": "opencv24" if legacy else "current",
                    "nativeDefaults": legacy["defaults"] if legacy else {},
                }
            ),
            encoding="utf-8",
        )
        runner = root / ("worker.py" if language == "python" else "worker.cjs")
        runner.write_text(
            PYTHON_WORKER if language == "python" else JS_WORKER, encoding="utf-8"
        )
        command = (
            [sys.executable, "-I", str(runner), str(root)]
            if language == "python"
            else [
                shutil.which("node"),
                "--max-old-space-size=256",
                str(runner),
                str(root),
            ]
        )
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
