# Detection sequences for OpenCV 2.4

Open the **Classroom / Učilnica** overlay, then select **Detection sequences / Zaporedja zaznavanja** below the eight foundation topics. Every sequence shows ordered processing cards, equations, tuning values, expected output, failure cases and references. **Build this algorithm in the application** imports the complete graph, selects OpenCV 2.4.13.7 and loads its test scene. It asks before replacing unsaved work. The library also lists these six recipes. Loading only registered IDs avoids accepting arbitrary code or graphs from iframe messages.

| Exercise | Ordered processing after RGB extraction | Demonstration |
| --- | --- | --- |
| Red part | R−G → threshold → opening → connected regions | One red rectangle survives; green and small specks do not |
| Bright regions | Luminance → Gaussian → threshold → connected regions | Two parts remain; holes remain background |
| Motion | Signed channel differences → vector magnitude → threshold → opening → connected regions | Empty first frame; changes on later frames |
| Straight lines | Luminance → Gaussian → Canny → Hough segments | Long boundary segments; short marks rejected |
| Edges with noise | Luminance → median → Laplacian → absolute value → threshold | Coherent rectangle edges after suppressing sparse impulse noise |
| Uneven light | Luminance → Gaussian → adaptive threshold → invert → connected regions | Dark bars across a smooth illumination gradient |

The five PNG test scenes are original synthetic images generated deterministically by `tools/build_detection_lessons.py`. Motion uses the existing moving demo. They are examples with measurable expected output, not evidence of industrial detection accuracy. Changing optics, illumination, geometry or material requires retuning and validation on representative data. Connected-region area uses actual foreground pixels with eight-connectivity, not contour polygon area. No physical dimension, calibrated accuracy or object identity is inferred from these masks.

## Book research

Read from the user's existing folder `D:\Dromation\Computer Vision`:

- **Joseph Howse, OpenCV Computer Vision with Python**, Packt, April 2013, ISBN 978-1-78216-392-3. Local filename: `OpenCV243 Computer Vision with Python.pdf`. Channel mixing: printed pp. 42–43, PDF pp. 55–56. Smoothing, edge responses and custom kernels: printed pp. 55–57, PDF pp. 68–70. Our edge exercise changes the original artistic outline example into float32 detection with an absolute Laplacian and threshold. Its median size, Laplacian stencil, synthetic input and purpose are explicitly different.
- **Emanuele Trucco and Alessandro Verri, Introductory Techniques for 3-D Computer Vision**, Prentice Hall, 1998. Local filename: `Zaznavanje - trucco_verri.pdf`. The scanned PDF places two printed pages on each sheet. Inspected printed pp. 52–53 (image noise, Gaussian and impulse models) on PDF p. 35, and printed pp. 68–69 (features and edge detection) on PDF p. 43. These support explaining why filtering and feature extraction are separate stages. This book provides mathematical background, not OpenCV API instructions.

The books stay in their original folder. Their PDF files, scans and code listings are not copied into the repository. The classroom contains original explanations, formulas, recipes and bibliographic page references.

## Official web references checked

- [OpenCV 2.4.13.7: Eroding and Dilating](https://docs.opencv.org/2.4.13.7/doc/tutorials/imgproc/erosion_dilatation/erosion_dilatation.html) — foreground growth/shrinkage and morphology.
- [OpenCV 2.4.13.7: Finding contours](https://docs.opencv.org/2.4.13.7/doc/tutorials/imgproc/shapedescriptors/find_contours/find_contours.html) — an example of segmentation/edges before shape analysis. Our area filter uses flood fill, not contour polygon area.
- [OpenCV 2.4.13.7: Hough Line Transform](https://docs.opencv.org/2.4.13.7/doc/tutorials/imgproc/imgtrans/hough_lines/hough_lines.html) — edge input and line-voting geometry.
- [OpenCV 2.4.13.7: adaptiveThreshold](https://docs.opencv.org/2.4.13.7/modules/imgproc/doc/miscellaneous_transformations.html#adaptivethreshold) — local Gaussian threshold, odd window and 8-bit input.
- The temporal example is an original SimpleMotocam exercise using the signed-channel approach from this project and a reference to mech-id-x's pinned `Test_za_podatke_While_Loop`. It is not attributed to a book's depth-camera or background-subtraction algorithm.

## Languages and exports

The six exercises have authored Slovenian and English prose and 19 marked machine drafts, using the same application language selection. The English original remains available for comparison. Equations, numbers, graphs and source records are shared and not translated. The four-language selector continues to control the eight foundation lessons. Full sequence code is a runnable Python orchestrator calling the native 2.4 engine; it is not advertised as a compiled C/C++/Java application. Download the algorithm JSON and test image, or use the main studio's Python export after loading the exercise.

Rebuild the authored content and test images with `python tools/build_detection_lessons.py`. Translate only the flat prose catalog with the existing local translator:

```powershell
.venv-translation\Scripts\python.exe tools/doc_translate/translate.py --input docs/opencv-2.4-manuals/learning/sequence-i18n/en.json --output docs/opencv-2.4-manuals/learning/sequence-i18n --no-bundle
.venv\Scripts\python.exe tools/build_detection_bundle.py
```

The bundle builder rejects stale or missing translations. `--preview` is for development only. Run `pytest tests_core/test_detection_sequences.py tests_core/test_studio_backend.py` with the worker installed, plus `npm run test:sequences` against a disposable studio. Native tests check pixel-level expected outcomes and custom-code export; browser checks exercise the same-window classroom, graph loading, source citations, language sync and responsive layout.
