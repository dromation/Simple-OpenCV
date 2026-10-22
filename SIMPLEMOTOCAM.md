# SimpleMotocam / Simple OpenCV

Working folder: `D:\Dromation\org\apps\betas\SimpleMotocam`.

This project extends [dromation/Simple-OpenCV](https://github.com/dromation/Simple-OpenCV)
at commit `c94281ee8d5468712b2e8e9ec63f04dd885f9757`.
The upstream license, Kivy application, examples and Git history are retained; the README now introduces the studio.
The experimental core lives in `src/simplemotocam` and can be used without Kivy.

## Run

Student documentation for OpenCV 2.4 is available offline in
`docs/opencv-2.4-manuals/`: three official PDF manuals plus a Slovenian
getting-started guide in that folder's `README.md`.
The multilingual interactive companion is `docs/opencv-2.4-manuals/learning/index.html`
(21 explanation languages; Python, C++, C and Java examples; equations and
numeric exercises). Open it directly or use `Open-OpenCV-Learning.cmd`.
Slovenian and English are authored; the other languages are machine drafts with
an English comparison view. Optional local M2M100/CTranslate2 tooling lives in
`tools/doc_translate/`; `Update-Learning-Translations.cmd` regenerates translations
after prose changes. Official English PDFs and source code examples are preserved.

The local Python 3.10 environment is already installed. In PowerShell:

```powershell
Set-Location 'D:\Dromation\org\apps\betas\SimpleMotocam'
.\.venv\Scripts\python.exe -m simplemotocam
.\.venv\Scripts\python.exe -m simplemotocam --show --frames 600
```

Double-click `Start-SimpleMotocam.cmd` for the new visual studio. See [the studio guide](docs/STUDIO.md).
The command-line `--show` option above opens the earlier synthetic channel viewer.
It shows RGB, separate colored R/G/B, confidence, signed dR, R-G, and edges.
Press Q or Escape to close. Signed display planes use mid-gray for zero;
the calculations retain floating point signed values.

Camera and video input are explicit:

```powershell
.\.venv\Scripts\python.exe -m simplemotocam --camera 0 --show --frames 1800
.\.venv\Scripts\python.exe -m simplemotocam --video 'D:\path\clip.avi' --show
.\.venv\Scripts\python.exe -m simplemotocam --blur 1.2 --edge scharr --output runs\experiment-01.json
.\.venv\Scripts\python.exe -m pytest
```

No camera is opened by the default experiment. No frames are saved automatically.
JSON output paths must be new; existing outputs are never overwritten.

To recreate the environment using an installed Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

`requirements-core-lock.txt` records the versions verified on this Windows/Python 3.10 setup.
For that environment, install it first, then install this project with
`pip install --no-deps -e .`.
The original `requirements.txt` remains an archival environment snapshot, not the
installation recipe for this core. It mixes two OpenCV distributions, legacy
SimpleCV/Kivy, machine learning and notebook dependencies. The legacy GUI has
not been migrated or validated against the new environment.

## Layout

| Location | Purpose |
| --- | --- |
| `smoto.py`, `smoto.kv`, `screens/` | Preserved legacy Kivy interface |
| `samples/`, `data/samples/`, `DLLmaker/` | Original examples and C++ experiments |
| `src/simplemotocam/channels.py` | Explicit channel order, normalization, confidence, signed differences |
| `src/simplemotocam/capture.py` | Camera/video resource ownership |
| `src/simplemotocam/algebra.py` | Synthetic channel expressions |
| `src/simplemotocam/operators.py` | Callable filters and edge estimators |
| `src/simplemotocam/pipeline.py` | Ordered processing and temporal state |
| `src/simplemotocam/geometry/` | Reserved for calibration and coordinates |
| `src/simplemotocam/metrology/` | Reserved for calibrated measurements and uncertainty |
| `experiments/channel_lab.py` | Small custom algebra/filter experiment |
| `tests_core/` | Hardware-independent tests for the new core |
| `docs/integration-2026-10-21.json` | Original file hashes and integration inventory |

## Channel contract

- Input: uint8 / 255, uint16 / 65535, or floating point already in [0, 1].
  Explicit order is RGB, BGR, RGBA or BGRA; OpenCV capture defaults to BGR.
  A 10/12-bit signal stored in uint16 must be normalized explicitly by the caller.
- Internal values: float32. R/G/B begin in [0, 1]; filters and algebra can produce
  negative values or values greater than 1. No implicit clipping of computations.
- These are decoded camera/image RGB values, not Bayer RAW or calibrated radiance.
  Gamma, exposure, white balance and camera processing remain part of the signal.
- `frame.rgb` preserves the unfiltered input; `result.channels` contains processed
  R/G/B and acquisition confidence A.
- A is a replaceable exposure-headroom heuristic:
  `clip(min(R,G,B,1-R,1-G,1-B) / 0.05, 0, 1)`.
  It is not a measured fourth sensor channel or a calibrated probability.
  It deliberately penalizes pixels clipped in any channel, including saturated
  colors. Later experiments should replace it with a calibrated quality model.
- Input alpha is retained as `frame.opacity`; it does not silently become A.
  Combine opacity into a confidence estimator explicitly if appropriate.
- Differences are signed `current - previous`: dR, dG, dB, dA.
  Filters run before temporal differencing; A is estimated from unfiltered RGB.
- The first frame has `temporal_ready=False` and an empty differences map.
  Resolution changes re-prime history. Call `pipeline.reset()` when changing
  source, calibration, confidence estimator or filter settings.
- Spatial synthetic channels are R-G and G-B. After priming, dR-dB, Euclidean
  RGB motion magnitude and confidence-weighted motion are also available.
  Confidence-weighted motion uses the minimum confidence of the two frames.
- Output arrays are read-only snapshots. Plugins must return finite arrays of
  the original H x W shape. They must not mutate inputs.
- Each pipeline belongs to one stream. There is no global state or automatic
  synchronization of multiple cameras.

## Write an experiment

```python
import numpy as np
from simplemotocam import ChannelPipeline
from simplemotocam.operators import Gaussian, ScharrMagnitude

pipeline = ChannelPipeline(
    filters=[Gaussian(sigma=1.0)],
    algebra={
        "red_opponent": lambda c: c["R"] - 0.5 * (c["G"] + c["B"]),
        "custom_energy": lambda c: c["red_opponent"] ** 2,
    },
    edges={"red_opponent": ScharrMagnitude()},
)
bgr = np.full((120, 160, 3), 96, dtype=np.uint8)
first = pipeline.process(bgr)
bgr[20:40, 30:50, 2] = 192
second = pipeline.process(bgr)
signed_red_change = second.differences["dR"]
```

An operator is any callable `plane -> plane`. Replace Gaussian/Sobel/Scharr with
your own numerical operator. Algebra is an ordered mapping of Python callables
over named channels; later expressions can use earlier ones. Names cannot
replace existing channels. Expressions execute on every frame, so guard
temporal inputs with `if "dR" in c` when needed. Edge input names must exist even
during priming; use a guarded synthetic channel for temporal edges.
Confidence estimators accept normalized RGB and return one [0, 1] plane.

The new package can later be called from the existing Kivy frame callback:
keep one pipeline per camera and pass each captured BGR frame to `process`.
This integration is not yet wired into the legacy GUI.

## Additional source collections

Additional historical examples are available in `external/`:

- `external/ComputerVision-MachineVision/samples_code/`: 21 original examples
  from the requested directory, plus the upstream README in its parent folder.
- `external/SI_Eksperimenti_Strojnega_Vida/`: all 28 repository files, including
  12 PNG experiment images.
- `external/opencv-2.4.13.7/`: complete official OpenCV 2.4.13.7 source snapshot,
  4209 files with original licenses. See `docs/opencv-2.4-reference.md` for the
  channel, arithmetic, filtering and geometry implementations. Source only;
  not built or installed into the Python environment.

See `external/README.md` for the source versions, compatibility notes and mapping
to future modules; `docs/external-sources.json` records every imported file hash.
These are preserved source references, not migrated executable core modules.

## Geometry and metrology roadmap

1. Attach acquisition timestamps, frame IDs and camera settings to captured data.
2. Calibrate intrinsics, lens distortion and coordinate frames against known targets.
3. Extract features from selected synthetic channels and compare edge estimators.
4. Map pixels to physical units only with a suitable calibration and scale reference.
5. Propagate calibration and detection uncertainty into measurements.

The geometry/metrology packages are explicit placeholders, not implemented
measurement tools. Temporal differences alone do not distinguish motion from
illumination changes; the modular operators allow experiments with those effects.

## Preservation and Git

The target folder already held 157 files without a .git directory. All 157
were preserved byte-for-byte and 15 missing upstream files were added.
67 existing paths differed from the clone at the byte level; Git reports
seven substantive file differences when line endings are ignored.
Their versions remain in the working tree, with upstream versions in Git history.

The active local branch is `experimental/simplemotocam`; `main` and `origin/main`
retain the upstream base. New core files and existing local changes are left
uncommitted for review. Nothing has been pushed.

The D: filesystem does not record Git ownership, so a Git safe-directory
exception was added for this exact project path only.

The visual studio now supports an explicit choice of OpenCV 2.4.13.7 or the installed current OpenCV processing engine. See [setup, supported blocks and exports](docs/OPENCV_BACKENDS.md). The earlier command-line viewer still uses the host OpenCV.
