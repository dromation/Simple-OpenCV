# SimpleMotocam multilingual learning guide

Open **index.html** in a regular web browser. No server, network connection or
extra installation is required. Select one of 21 explanation languages
independently of the code language (Python, C++, C or Java).

The eight topics cover RGB, signed differences, channel algebra, derived
confidence, filter kernels, spatial derivatives, thresholds and physical scale.
Each includes an equation, variable definitions, a worked example, assumptions
and code. Sliders recalculate learning values in the browser; they do not modify
the application or its code.

Slovenian and English are project-authored. The other 19 languages are labelled
machine translations, pending technical and language review. The English
original is expanded by default for comparison. Arabic uses right-to-left
prose while code and equations retain left-to-right direction. Official PDFs
remain in English. Code and equations are shared by all explanation languages.
For future translations see `tools/doc_translate/` at the project root and
run `Update-Learning-Translations.cmd` after changing the source prose.

## Programming environments

- **Python:** standalone Python 3 scripts, numerically verified in the project
  environment with NumPy 2.2.6 and OpenCV 4.14.0. Save a `.py` example using the
  button and run it with the project's `.venv\Scripts\python.exe`.
  These scripts have not been tested with OpenCV 2.4 or Python 2.
- **C++:** OpenCV 2.4 API fragments. Typically include `opencv2/opencv.hpp` and
  `<vector>`, supply `cv::Mat` inputs and link a compiled OpenCV library.
  Scalar examples use the additional standard headers noted in the code.
  Fragments are not standalone programs and have not been compiled.
- **C:** legacy OpenCV 2.4 `CvMat*` / `CvArr*` API, with headers
  `opencv2/core/core_c.h` and `opencv2/imgproc/imgproc_c.h`. Allocate the stated
  destination matrices and release owned matrices with `cvReleaseMat` after use.
  Scalar examples use C99. Fragments have not been compiled.
- **Java:** fragments target OpenCV 2.4 bindings. Import `org.opencv.core.*`,
  `org.opencv.imgproc.Imgproc` and `java.util.*`; provide matching JAR/native
  libraries and call `System.loadLibrary(Core.NATIVE_LIBRARY_NAME)` before OpenCV
  operations. Border constants used here belong to `Imgproc` in 2.4; newer
  versions expose them in `Core`. Fragments have not been compiled or executed.

C/C++/Java downloads use `.txt` suffixes because they require a surrounding program.
The language selector does not automatically translate between API generations.

## Mathematical assumptions

Convert images to float32 before arithmetic. Differences retain their sign;
magnitudes are not derivatives per second. `filter2D` computes correlation, so
asymmetric kernel orientation matters. A is the project heuristic described in
`MODEL.md`. A uniform mm/pixel scale requires suitable capture geometry;
application metrology remains unimplemented.

Each lesson links its API source. `verification.json` records the checks performed
and their limitations.

## Detection sequences / Zaporedja zaznavanja

The classroom also contains six complete OpenCV 2.4 detection exercises with ordered blocks, mathematics, parameters, failure cases and book/web references. Load an exercise and its synthetic scene directly into the studio. The sequence orchestrator is Python; the four-language examples above describe the original foundation topics. See [sources and verification](../../DETECTION_SEQUENCES.md).
