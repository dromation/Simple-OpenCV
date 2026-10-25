"""Build isolated OpenCV 2.4 core/imgproc and the Studio worker (Windows/MSVC).

The pinned upstream source is copied; the reference snapshot is never edited.
Install CMake 3.31.x under work/build-tools or pass --cmake explicitly.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def visual_studio():
    locator = (
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    result = subprocess.check_output(
        [
            str(locator),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        text=True,
    ).strip()
    if not result:
        raise RuntimeError("Install Visual Studio C++ build tools")
    return Path(result)


def build():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cmake", type=Path, default=ROOT / "work/build-tools/cmake/data/bin/cmake.exe"
    )
    args = parser.parse_args()
    original = ROOT / "external/opencv-2.4.13.7"
    source = ROOT / "work/opencv24-source"
    build_dir = ROOT / "work/opencv24-build"
    install = ROOT / ".motocam/backends/opencv24"
    if not original.is_dir():
        raise RuntimeError("Fetch the pinned OpenCV 2.4.13.7 reference source first")
    manifest = json.loads(
        (ROOT / "docs/opencv-2.4.13.7-manifest.json").read_text(encoding="utf-8")
    )
    for entry in manifest["files"]:
        path = original / entry["path"]
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]
        ):
            raise RuntimeError(f"Reference source differs from pinned manifest: {path}")
    if not source.exists():
        shutil.copytree(original, source, ignore=shutil.ignore_patterns(".git"))
    for entry in manifest["files"]:
        path = source / entry["path"]
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]
        ):
            raise RuntimeError(
                f"Build source differs from pinned manifest: {path}; use a fresh workspace"
            )
    vs = visual_studio()
    vcvars = vs / "VC/Auxiliary/Build/vcvars64.bat"
    # Capture the compiler's environment in memory, never log credentials/environment.
    batch = ROOT / "work/opencv24-env.cmd"
    batch.write_text(
        '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\nset\n',
        encoding="utf-8",
    )
    text = subprocess.check_output(
        ["cmd.exe", "/d", "/c", str(batch)], text=True, errors="replace"
    )
    env = {key.upper(): value for key, value in os.environ.items()}
    for line in text.splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            env[key.upper()] = value
    ninja = vs / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
    flags = [
        "-DCMAKE_BUILD_TYPE=Release",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_WITH_STATIC_CRT=ON",
        "-DENABLE_PRECOMPILED_HEADERS=OFF",
        "-DBUILD_TESTS=OFF",
        "-DBUILD_PERF_TESTS=OFF",
        "-DBUILD_EXAMPLES=OFF",
        "-DBUILD_DOCS=OFF",
        "-DBUILD_opencv_apps=OFF",
        "-DBUILD_ZLIB=ON",
        "-DOpenCV_ARCH=x64",
        "-DOpenCV_RUNTIME=vc17",
    ]
    flags += [
        "-D" + name + "=OFF"
        for name in set(
            re.findall(
                r"OCV_OPTION\((WITH_\w+)", (source / "CMakeLists.txt").read_text()
            )
        )
    ]
    flags += [
        "-DBUILD_opencv_"
        + p.name
        + "="
        + ("ON" if p.name in ("core", "imgproc") else "OFF")
        for p in (source / "modules").iterdir()
        if p.is_dir()
    ]
    commands = [
        [
            str(args.cmake),
            "-S",
            str(source),
            "-B",
            str(build_dir),
            "-G",
            "Ninja",
            "-DCMAKE_MAKE_PROGRAM=" + str(ninja),
            "-DCMAKE_INSTALL_PREFIX=" + str(install),
            *flags,
        ],
        [
            str(args.cmake),
            "--build",
            str(build_dir),
            "--target",
            "opencv_core",
            "opencv_imgproc",
            "--parallel",
            "4",
        ],
    ]
    worker_build = ROOT / "work/opencv24-worker-build"
    commands += [
        [
            str(args.cmake),
            "-S",
            str(ROOT / "tools/native_opencv24"),
            "-B",
            str(worker_build),
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_MAKE_PROGRAM=" + str(ninja),
            "-DOPENCV24_SOURCE=" + str(source),
            "-DOPENCV24_BUILD=" + str(build_dir),
        ],
        [str(args.cmake), "--build", str(worker_build), "--parallel", "4"],
    ]
    log = ROOT / "work/opencv24-build.log"
    with log.open("w", encoding="utf-8") as handle:
        for command in commands:
            print(
                "OpenCV 2.4 build: " + ("configure" if "-S" in command else "compile"),
                flush=True,
            )
            result = subprocess.run(
                command, env=env, stdout=handle, stderr=subprocess.STDOUT
            )
            handle.flush()
            if result.returncode:
                raise RuntimeError(f"Build failed; inspect {log}")
    install.mkdir(parents=True, exist_ok=True)
    worker = install / "simplemotocam_opencv24.exe"
    shutil.copy2(worker_build / worker.name, worker)
    shutil.copy2(original / "LICENSE", install / "OpenCV-LICENSE.txt")
    shutil.copy2(ROOT / "LICENSE", install / "SimpleMotocam-LICENSE.txt")
    zlib = (original / "3rdparty/zlib/zlib.h").read_text(encoding="utf-8")
    (install / "zlib-LICENSE.txt").write_text(
        zlib[: zlib.index("*/") + 2] + "\n", encoding="utf-8"
    )
    manifest = json.loads(
        (ROOT / "docs/opencv-2.4.13.7-manifest.json").read_text(encoding="utf-8")
    )
    (install / "build-info.json").write_text(
        json.dumps(
            {
                "opencv": "2.4.13.7",
                "protocol": 2,
                "source_commit": manifest["commit"],
                "platform": "Windows x64",
                "modules": ["core", "imgproc"],
                "worker_sha256": hashlib.sha256(worker.read_bytes()).hexdigest(),
                "source": "https://github.com/opencv/opencv/tree/2.4.13.7",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    version = subprocess.check_output([str(worker), "--version"], text=True).strip()
    if version != "2.4.13.7":
        raise RuntimeError("Unexpected OpenCV worker version")
    print("Installed genuine OpenCV " + version + " worker: " + str(worker), flush=True)


if __name__ == "__main__":
    build()
