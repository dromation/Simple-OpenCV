# Using the visual studio

Run `Start-SimpleMotocam.cmd` after `Install-SimpleMotocam.cmd`, or `python -m simplemotocam.studio`. The server listens only on `127.0.0.1:8765`. Stop it with Ctrl+C in its terminal. Use `--port 8766` if that port is occupied. This is a single-user, shared local session; multiple tabs control the same running algorithm.

## Make an experiment

1. Start with the moving synthetic part. **Zaženi** runs frames, **Premor** pauses, and **Ena sličica** advances one frame. Selecting **Zajem** lets you choose a camera index, upload a still image or upload a video (100 MB maximum). Camera access starts only when processing a frame. Closing the browser does not stop the Python server; pause the camera or stop the server when finished.
2. Click a block to see parameters and a mathematical explanation. Drag a library block onto the canvas to insert it, or click it to append. Drag existing cards or use ↑ / ↓ to reorder. The source and RGB normalization remain first.
3. Select input channels from earlier blocks. Name each output uniquely. Removing or reordering a required input produces a validation error: processing stops until you repair it or use Undo. A failed edit does not replace the server's last valid algorithm.
4. Use weight sliders or edit the algebra expression directly. For example `wR*R + wG*G + wB*B` combines colours, while `sqrt(dR**2 + dG**2 + dB**2)` computes colour-change magnitude. `dR` etc. require an earlier difference block.
5. Add Gaussian/median filters, a custom 3×3 correlation kernel, Sobel/Scharr edge magnitude or a threshold. Turn off an operator to pass its input through unchanged. Algebra, channel extraction and temporal difference are structural blocks and cannot be bypassed.
6. Select any output channel in the signal/result previews. Display gain changes only image rendering, never the numerical arrays. Signed signal display maps zero to mid-grey. Unsigned result display clips negative values to black; min/max/mean below the image still report the raw values.
7. **Shrani stanje** creates a new timestamped local JSON record and downloads a portable JSON configuration. **Odpri** loads a saved record or imports JSON. Saving never overwrites an earlier record. Undo/Redo applies to graph and parameter edits during this session.
8. **Izvozi Python** downloads a standalone script with the exact engine and current state embedded. It requires NumPy and OpenCV but no SimpleMotocam installation. An OpenCV 2.4 export additionally requires the native worker; see [portable exports](OPENCV_BACKENDS.md). Run `python simplemotocam_algorithm.py --frames 120 --show`, or supply `--camera 0`, `--video clip.mp4` or `--image sample.png`. The exported orchestrator is Python. Blocks marked JavaScript execute using Node.js, which must also be installed. C/C++/Java custom blocks also execute with an installed compiler/JDK; the lesson selectors remain educational snippets.

## Numeric contract

- OpenCV BGR uint8 is converted to RGB float32 in [0,1]; uint16 and normalized float input are supported by the engine.
- `A = clip(min(R,G,B,1-R,1-G,1-B) / 0.05, 0, 1)` is an exposure-margin heuristic. It is not a measured alpha channel or a calibrated probability. The confidence block computes a separately named channel with an editable margin.
- `dC = C(t) - C(t−1)` retains sign. The first frame, a changed frame size or an algorithm/source change yields zero differences. Display/language changes preserve temporal history.
- No per-frame min/max normalization is applied. Most filters operate on float32; the 8-bit algorithms described below explicitly quantize their inputs. Gaussian and custom kernels use reflected borders. The custom kernel is **correlation**, matching `filter2D`, rather than a mathematically flipped convolution.
- Sobel kernels are normalized to a unit response on a unit linear ramp; Scharr uses scale 1/32. Gradient magnitude is `sqrt(dx²+dy²)`. The UI size choices are 3/5/7 for Sobel and 3/5 for float median.
- Threshold returns 1 only when input is strictly greater than the threshold. Division by zero, invalid square roots and other nonfinite results fail visibly. The restricted expression language cannot access Python objects, files or imports.
- Live processing downsizes sources larger than 960 pixels on their longest side. Exported scripts process the original input size. Consequently spatial filters on large sources will differ between the resized preview and a full-resolution export; use matching resolutions when comparing results.

## Learning languages

The application header selects one of **21 languages** for buttons, block names, parameters, status messages and the lesson inspector. The classroom opens as an in-app overlay from the header, library or full-lesson button. Its language and code-example selections stay synchronized with the studio. Close it with × or Escape; your graph and classroom exercise values remain in place. Language changes do not advance frames or reset numerical history. Raw diagnostic details from the numerical engine retain their original technical wording.

Removable block cards have × at the top-right corner; the fixed source and RGB blocks remain required. Undo restores a removed block. The learning companion still works independently when opened directly and provides formulas and Python/C++/C/Java examples. English and Slovenian interface text and lessons are authored; 19 translations are clearly marked machine drafts with an expanded English original. They need human technical review. The companion contains eight foundation topics plus six runnable detection sequences, not a translation of every OpenCV manual. The original three OpenCV 2.4 PDFs remain English and unchanged.

## Local files and reproducibility

`.motocam/projects/` stores configurations; `.motocam/uploads/` stores imported media under content-derived names. Both are ignored by Git. JSON state refers to an uploaded asset by ID and does not embed the image/video. On another computer, select the media again; the export requires an explicit input path for non-demo sources. Camera indices and available codecs depend on the machine.

OpenCV 2.4.13.7 is the primary processing engine. The header also offers the installed current OpenCV. All 28 registered block kinds are supported in the 2.4 profile, including exact connected-region area filtering and custom Python/JavaScript/C/C++/Java channel functions. See [backend setup and compatibility](OPENCV_BACKENDS.md). Source capture and preview rendering remain shared host services. The legacy Kivy application and its samples are preserved separately. Geometry and metrology are reserved extension modules, not implemented calibrated measurements.


## Expanded block library

Search remains available above a category filter and a grouped dropdown containing **all registered blocks, mathematical functions, recipes, source references, and the installed OpenCV top-level API**. Cards show the first 45 matches; the dropdown includes every match. API entries display the installed function signature/documentation or constant value. They are reference entries, not automatically executable blocks: functions with incompatible input/output shapes need an explicit adapter or a custom block.

The library has **28 block kinds** (including the fixed source and RGB blocks): the original 11 plus luma, RGB color distance, inversion, box/bilateral filters, Laplacian, Canny, Otsu/adaptive thresholding, connected-component filtering, Hough line masks, custom code, and five morphological operations. The mathematical functions `abs`, `sqrt`, `minimum`, `maximum`, and `clip` insert editable algebra blocks. Names and formulas are preserved when the interface language changes.

**Your adapted examples** includes four modern, runnable adaptations from mech-id-x's collections and a simple RGB contrast recipe, plus the repository presets. The adaptations cover color distance with segmentation, blob filtering, line detection, and temporal-change segmentation. Their detail panels link to pinned original source files. They are partial adaptations: legacy template matching, robotics, missing camera/template assets and calibrated distance calculations are not reproduced. All 37 original scripts from the two collections are also browsable as references; opening one never executes it.

Select an algorithm and choose **Save block with dependencies**. It saves the selected block and all upstream blocks as a new reusable recipe under `.motocam/blocks/`. Saved projects also appear in the library. Loading a recipe replaces the current graph after the existing unsaved-changes confirmation; it keeps the interface language. Recipes are deliberately complete dependency chains, not silently rewired fragments. Existing files are never overwritten.

## Write and run a custom block

Add **Empty block · custom code**. An empty editor passes the selected input through unchanged. Select **Python** or **JavaScript**, enter a function, then choose **Apply and run code**. Code is saved in the project and embedded in exports. Apply pending editor changes before saving or exporting. The output selector switches to the custom result after Apply.

Python receives a dictionary of all upstream two-dimensional float32 channels and the block's parameter dictionary. NumPy is available as `np`. In the primary OpenCV 2.4 profile, use `cv24.run(kind, plane, **params)` for native operations; it is a limited explicit bridge, not the full legacy Python bindings. In the current profile, the installed OpenCV is available as `cv2`:

```python
def process(channels, params):
    return (channels["R"] - channels["G"]) * params["gain"]
```

JavaScript receives flat row-major Float32Array channels, parameters and `[height, width]`. Node.js must be installed and available on PATH:

```javascript
function process(channels, params, shape) {
  return channels.R.map((r, i) => (r - channels.G[i]) * params.gain);
}
```

Return exactly one finite H × W channel (flat H*W values for JavaScript). The `gain` parameter is passed to your function; it is separate from display gain. Select earlier channel names from the input dropdown or access them directly in `channels`. A fresh process executes each custom block for each frame; globals do not persist between frames. Worker startup and binary transfers make custom code slower than native blocks. Time limit defaults to 5 seconds (0.1–30 seconds allowed). Exceptions, timeouts, wrong shapes and nonfinite outputs become visible errors and do not advance temporal history.

**Custom code runs with your local user permissions.** A worker process and timeout are reliability controls, not a security sandbox or a memory/process-tree limit. Run only code you trust. Importing/configuring a custom-code recipe does not execute it; Run, Single frame or Apply starts execution. External Python 2 scripts and API reference entries are never automatically executed. The restricted algebra block continues to reject arbitrary Python access.

The library has a direct **Empty block · custom code** button. Select a listed language or enter any language ID. Language changes preserve separate drafts in the project; they do not translate code. **Keep code as draft** accepts unfinished code and bypasses the block. Save the project to persist all language drafts on disk. **Apply and run** requires an available compatible adapter and enables the block. C, C++ and Java have built-in compiler adapters and starter functions; execution requires the matching compiler/JDK. See [compiled block examples](COMPILED_BLOCKS.md). See [arbitrary languages and the external adapter contract](CUSTOM_CODE_ADAPTERS.md).

## Additional numerical contracts

- **Luma:** `0.299 R + 0.587 G + 0.114 B` on the captured RGB samples; no gamma linearization or physical radiometric calibration.
- **Color distance:** Euclidean distance from the target RGB triple, divided by `sqrt(3)`. Targets are normalized [0,1]. Inversion is exactly `1 - input`, with no clipping.
- **Canny/Otsu/adaptive threshold:** explicitly map `round(255 * clip(input,0,1))` to uint8. Results are binary float32 {0,1}. Canny uses 3×3 derivatives and L2 gradient, thresholds in [0,255], with low ≤ high. Adaptive threshold uses the Gaussian neighborhood mean minus the signed offset in 8-bit intensity units. Display gain has no effect.
- **Morphology:** rectangular all-ones kernels, editable odd size 3–15 and 1–10 iterations, OpenCV default morphology borders. Opening/closing use the corresponding OpenCV composite operations; the gradient is dilation minus erosion.
- **Laplacian:** signed four-neighbor discrete Laplacian (`ksize=1`). Box filtering uses a normalized neighborhood average. Bilateral color sigma is measured in normalized channel units, spatial sigma in pixels.
- **Components:** foreground is `input > 0`, connectivity is 8. Returns a binary mask retaining components with area ≥ minArea; the background is always excluded.
- **Hough:** positive input pixels become a binary edge map. Probabilistic Hough uses rho=1 px and theta=π/180, then draws detected segments with thickness 1 into a binary mask. Use Canny upstream. This is not calibrated metrology.

Primary API references: [OpenCV thresholding](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html), [OpenCV image filtering](https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html), and [OpenCV feature detection](https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html).

## Updating execution backends

C, C++ and Java are available on all 25 editable block kinds when their
toolchains are installed. Algebra, confidence, luminance, color distance and
inversion compile to the selected language. The 19 OpenCV operations use a
compiled process adapter to the selected shared engine, preserving its version
and numerical behavior. This is not a direct C/Java binding for the full OpenCV
API. The inspector explains which mode is active. Source, channel extraction
and temporal differences stay shared. See [compiler setup and examples](COMPILED_BLOCKS.md).

`studio_runtime.py` defines runtime contract version 1, capability metadata, availability checks, starter code and worker adapters. `/api/library` and bootstrap publish the installed capabilities. Project nodes store `runtime`; omitted means Python for backwards compatibility. Disabled custom blocks may retain arbitrary language drafts, while enabled blocks require a compatible installed runtime. Optional `codeDrafts` stores each language's source. The host reads external adapters from `SIMPLEMOTOCAM_RUNTIME_CONFIG`; commands are never taken from imported project data. Reload the page after updating the configuration.

To extend a runtime, implement its availability probe and worker command/serialization, declare supported block kinds, validate code without executing it during import, and add numerical parity/timeout/export tests. Keep the finite float32 H × W contract. `export_python` embeds the complete runtime module and engine; avoid package-only dependencies or add explicit export support. The full Python application remains the orchestrator for mixed-language graphs.

In the classroom, select **Zaporedja zaznavanja / Detection sequences** below the foundation topics. Every sequence shows its block order, mathematics, tuning suggestions, expected result, failure cases and book/web references. **Build this algorithm** loads the complete 2.4 graph with its synthetic test scene; unsaved work requires confirmation. The same recipes appear in the block library. See [detailed sequence documentation](DETECTION_SEQUENCES.md).

**Additional algorithms / Dodatni algoritmi** opens a separate, initially closed collection for mech-id-x adaptations, original source references, teaching recipes and saved user algorithms. These recipes do not populate the default left-hand card list. Search and the complete dropdown remain available; selecting a saved algorithm still opens its details before loading it.
