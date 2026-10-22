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
8. **Izvozi Python** downloads a standalone script with the exact engine and current state embedded. It requires NumPy and OpenCV but no SimpleMotocam installation. Run `python simplemotocam_algorithm.py --frames 120 --show`, or supply `--camera 0`, `--video clip.mp4` or `--image sample.png`. Export execution is Python; the inspector's C/C++/Java selections are educational snippets, not full pipeline exporters.

## Numeric contract

- OpenCV BGR uint8 is converted to RGB float32 in [0,1]; uint16 and normalized float input are supported by the engine.
- `A = clip(min(R,G,B,1-R,1-G,1-B) / 0.05, 0, 1)` is an exposure-margin heuristic. It is not a measured alpha channel or a calibrated probability. The confidence block computes a separately named channel with an editable margin.
- `dC = C(t) - C(t−1)` retains sign. The first frame, a changed frame size or an algorithm/source change yields zero differences. Display/language changes preserve temporal history.
- No per-frame min/max normalization is applied. Filters operate on float32. Gaussian and custom kernels use reflected borders. The custom kernel is **correlation**, matching `filter2D`, rather than a mathematically flipped convolution.
- Sobel kernels are normalized to a unit response on a unit linear ramp; Scharr uses scale 1/32. Gradient magnitude is `sqrt(dx²+dy²)`. The UI size choices are 3/5/7 for Sobel and 3/5 for float median.
- Threshold returns 1 only when input is strictly greater than the threshold. Division by zero, invalid square roots and other nonfinite results fail visibly. The restricted expression language cannot access Python objects, files or imports.
- Live processing downsizes sources larger than 960 pixels on their longest side. Exported scripts process the original input size. Consequently spatial filters on large sources will differ between the resized preview and a full-resolution export; use matching resolutions when comparing results.

## Learning languages

The application header selects one of **21 languages** for buttons, block names, parameters, status messages and the lesson inspector. The classroom opens as an in-app overlay from the header, library or full-lesson button. Its language and code-example selections stay synchronized with the studio. Close it with × or Escape; your graph and classroom exercise values remain in place. Language changes do not advance frames or reset numerical history. Raw diagnostic details from the numerical engine retain their original technical wording.

Removable block cards have × at the top-right corner; the fixed source and RGB blocks remain required. Undo restores a removed block. The learning companion still works independently when opened directly and provides formulas and Python/C++/C/Java examples. English and Slovenian interface text and lessons are authored; 19 translations are clearly marked machine drafts with an expanded English original. They need human technical review. This is an eight-topic learning companion, not a translation of every OpenCV manual. The original three OpenCV 2.4 PDFs remain English and unchanged.

## Local files and reproducibility

`.motocam/projects/` stores configurations; `.motocam/uploads/` stores imported media under content-derived names. Both are ignored by Git. JSON state refers to an uploaded asset by ID and does not embed the image/video. On another computer, select the media again; the export requires an explicit input path for non-demo sources. Camera indices and available codecs depend on the machine.

The executable application uses OpenCV 4, while OpenCV 2.4 source and manuals remain historical references. The legacy Kivy application and its samples are preserved separately. Geometry and metrology are reserved extension modules, not implemented calibrated measurements.
