# Choose an OpenCV processing engine

**OpenCV 2.4.13.7 is the primary engine for new application sessions.** The installer builds it and startup requires it. To deliberately start with the installed current engine, pass `--backend current` (or set `SIMPLEMOTOCAM_DEFAULT_BACKEND=current`). There is no automatic fallback when the legacy worker is missing or outdated. Previously saved states keep their explicit version; old unversioned states retain their original current-OpenCV interpretation.

Use **OpenCV za obdelavo / OpenCV processing engine** in the application header. Choose **OpenCV 2.4.13.7** or **Current OpenCV** (the exact installed version is displayed; this is not an automatic upgrade). A successful switch preserves nodes and parameters, resets temporal history and pauses playback. Save state to record the engine ID and exact version with the algorithm. Older states without an engine retain their existing current-OpenCV behavior.

Missing engines and version mismatches fail visibly. No operation silently falls back to another OpenCV version. An incompatible graph remains unchanged after a failed switch. Select an explicitly supported configuration before switching.

## What runs where

The primary worker contains genuine, unmodified OpenCV **2.4.13.7 core and imgproc**, compiled from commit `51cfa519249c89d24035b3f96315ad997deb300f`. It executes 19 block kinds: Gaussian, median, box, bilateral, custom 3×3 kernel, Laplacian, Sobel, Scharr, threshold, Canny, Otsu, adaptive threshold, Hough line mask, erosion, dilation, opening, closing, morphological gradient and connected-region area filtering. The latter uses native 2.4 `floodFill` with eight-connectivity and exact foreground pixel counts, retaining holes.

Eight shared blocks remain version-independent: source plumbing, RGB extraction, channel differences, channel algebra, confidence, luminance, color distance and inversion. Together with the custom block, **all 28 registered block kinds** work in the legacy profile. Custom Python uses NumPy plus the explicit `cv24.run` bridge; custom JavaScript uses Node.js for channel arithmetic. The library disables incompatible blocks and templates and shows version-appropriate API references. Supported JavaScript arithmetic blocks still use Node.js when selected.

Camera/video decoding, synthetic source generation, preview resizing/encoding and the Python application remain shared host services using the installed current OpenCV. Selecting 2.4 does not replace the host Python package or install all legacy OpenCV modules. The worker is an internal C++ bridge; general user-written C/C++/Java code adapters are still extension points. This does not claim coverage of every historical OpenCV module or the complete old Python bindings.

Each legacy operation launches a separate native process with float32 plane files, a validated parameter request and a ten-second timeout. This favors isolation and reproducibility over high frame rates. Current and legacy implementations can differ numerically; a saved version identifies the intended implementation.

## Build on Windows x64

Install Visual Studio or Build Tools with the C++ desktop tools, Windows SDK and CMake/Ninja component. `Install-SimpleMotocam.cmd` installs the Python environment and calls `Install-OpenCV24.cmd`. The latter keeps an up-to-date worker and builds a missing/outdated one. For manual setup, install the normal Python environment first. From the project folder:

```powershell
.venv\Scripts\python.exe tools/fetch_references.py opencv-2.4.13.7
.venv\Scripts\python.exe -m pip install --target work/build-tools cmake==3.31.10
.venv\Scripts\python.exe tools/build_opencv24.py
.motocam\backends\opencv24\simplemotocam_opencv24.exe --version
```

The last command must print `2.4.13.7`. Restart the application after installation. The builder copies the pinned source into ignored `work/opencv24-source/`, compiles only core/imgproc plus bundled zlib, and installs the worker under ignored `.motocam/backends/opencv24/`. Upstream files in `external/` remain unchanged. The build log is `work/opencv24-build.log`. The output includes dependency notices and `build-info.json` with the source revision and executable hash. Existing build/source copies are reused; after intentionally changing sources, use a fresh workspace to avoid stale cached builds. Other platforms need a corresponding native build; this script targets Windows x64.

A worker can also be selected with the `SIMPLEMOTOCAM_OPENCV24_WORKER` environment variable, pointing to its full executable path. An invalid explicit path is an error, not permission to select another installation. Worker protocol 2 is required; an old 0.4.0 worker must be rebuilt.

## Portable exports

Python exports embed the graph, selected version and processing code. Current-profile exports require NumPy and the matching OpenCV package. Legacy exports additionally require the native worker. On the original computer, the export remembers the installed worker path. To move it, copy the worker and its license/build-info files into an `opencv24/` folder beside the exported script, or set the environment variable above. Keep all bundled notices when distributing binaries. Node.js is needed for any JavaScript blocks. The JSON state alone does not contain the native executable or input media.

## Extend and verify

`studio_backend.py` defines discovery, version validation, supported kinds and the request protocol. `tools/native_opencv24/worker.cpp` implements the native operations. Add a kind only after both its implementation and numerical contract are tested. `studio_catalog.py` exposes compatibility to the UI. General programming-language adapters remain in `studio_runtime.py`; they are separate from the selected OpenCV version.

Run `python -m pytest tests_core/test_studio_backend.py -q` with the worker installed to exercise actual 2.4 operations, numerical comparisons, failed-switch preservation and saved/exported reproducibility. Native tests skip when the optional worker is absent. `tools/browser-tests/verify_backends.cjs` checks the real selector against a disposable server with both engines available.

## Custom code with OpenCV 2.4

A custom Python block receives `np`, `channels`, `params` and a limited `cv24` bridge. Its `run` method accepts a native block kind, a finite float32 plane of the same size, and the numeric/kernel parameters shown in the library. Defaults are supplied for omitted native parameters. Input/output names are not operation parameters. For example:

```python
def process(channels, params):
    contrast = channels["R"] - channels["G"]
    return cv24.run("gaussian", contrast, size=3, sigma=1)
```

`cv24.__version__` is `2.4.13.7`. Normal `import cv2` resolves to this limited bridge in that worker, so an unsupported call raises a clear error rather than using OpenCV 4. This is not a complete legacy `cv2` module. Use `cv24.run("components", mask, minArea=100)` for eight-connected area filtering. Existing Python code written against the full modern `cv2` API may need adapting when switching profiles. Imported custom code still waits for explicit Apply/Run; code has local-user permissions and is not a security sandbox. The timeout covers the complete custom operation including nested native work. These custom blocks and their selected engine survive state saving and Python export.

## Learning detection pipelines

The in-app classroom now includes six source-referenced, runnable [detection sequences](DETECTION_SEQUENCES.md), with five original synthetic test scenes. Loading one selects OpenCV 2.4 explicitly and asks before replacing unsaved work. Individual intermediate channels remain inspectable in the normal studio.
