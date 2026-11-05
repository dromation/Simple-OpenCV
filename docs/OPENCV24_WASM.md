# Genuine OpenCV 2.4 in the HTML edition

The default browser engine is OpenCV **2.4.13.7**, compiled from source commit
`51cfa519249c89d24035b3f96315ad997deb300f`. It contains the actual `core` and
`imgproc` implementations. It is not an alias or compatibility label for 4.x.
OpenCV.js 4.13.0 remains an optional engine with its own binary and version probe.

`tools/native_opencv24/operations.hpp` supplies the same 19 operations to both
the native file-based worker and the memory-only WebAssembly adapter. The JS
bridge transfers float32 planes, explicit round-to-even byte planes and numeric
parameters. C++ errors are caught and returned to the UI. No operation silently
falls back to OpenCV 4. The shared browser layer supplies RGB, derived confidence,
frame differences, channel algebra and JavaScript custom blocks.

This build does not expose every OpenCV 2.4 module or provide Python/C/C++/Java
compilers in the browser. Media input uses browser image/video/camera APIs.

## Rebuild (Linux or WSL, no administrator access)

Use Python 3.10+, CMake 3.x and make. Install the pinned Emscripten SDK in a
separate directory, following its [official build instructions](https://emscripten.org/docs/compiling/Building-Projects.html):

```sh
git clone --depth 1 --branch 3.1.74 https://github.com/emscripten-core/emsdk.git /tmp/simplemotocam-emsdk
/tmp/simplemotocam-emsdk/emsdk install 3.1.74
/tmp/simplemotocam-emsdk/emsdk activate 3.1.74
source /tmp/simplemotocam-emsdk/emsdk_env.sh
python tools/fetch_references.py opencv-2.4.13.7
python tools/build_opencv24_wasm.py --build-dir /tmp/simplemotocam-opencv24-wasm --jobs 2
python tools/package_static.py
```

The builder verifies every original source file against the existing manifest,
disables optional modules and platform-specific optimizations, catches C++
exceptions, embeds WASM in one JS asset, probes the compiled version using Node,
and records the binary SHA-256. Nothing is installed system-wide. A separate
output directory preserves native build artifacts. The committed browser binary
means ordinary users only need the final ZIP, not this toolchain.

The package includes both engines and licenses. No CDN, special WASM MIME type,
SharedArrayBuffer isolation headers or server-side executable is required. Serve
through HTTP(S); `file://` does not allow ordinary external Workers.

## Validation

Build the native 2.4 worker (`tools/build_opencv24.py` on Windows or
`tools/build_opencv24_linux.py` on Linux). Then:

```sh
python tools/browser-tests/static_reference.py
python tools/package_static.py
python -m http.server 8780 --bind 127.0.0.1 --directory dist
# In another terminal after npm ci --prefix tools/browser-tests:
node tools/browser-tests/verify_static.cjs
node tools/browser-tests/verify_static_numeric.cjs
```

Tests compare WASM results to the genuine native 2.4 worker, verify the optional
4.x engine, engine switches/history resets, saved states, executable exports,
media persistence, classroom sequences and code timeout/recovery. Floating-point
rounding across CPU/WASM can differ slightly; comparisons use an explicit tolerance.
