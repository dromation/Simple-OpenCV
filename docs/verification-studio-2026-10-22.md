# Studio verification — 2026-10-22

Verified locally on Windows, Python 3.10.11, NumPy 2.2.6, OpenCV 4.14.0 and Chrome driven by Playwright 1.62.1.

- `python -m pytest`: **47 passed**. Covers core channels/operators, signed differences, first-frame handling, safe expression rejection, error-history isolation, custom kernels, confidence, bypass/order validation, state persistence, HTTP token/origin checks, image/video sources and standalone export.
- `python -m pytest tools/doc_translate/test_translate.py`: **5 passed**. Translation protection checks.
- `tools/browser-tests/verify.cjs`: **passed**. Actual drag insertion, reorder controls, invalid formula recovery through Undo, JSON save/load equality, executing the downloaded Python export, image upload, all 21 explanation languages, Arabic RTL, all four code-example languages, no external frontend requests, no JavaScript errors and no horizontal overflow at 390/768/1512 pixel viewport widths.
- Standalone export matches every numerical channel of the studio engine on five deterministic synthetic frames, bit for bit. This comparison uses identical input dimensions.
- README screenshots are captures of the running application with the synthetic source, not the earlier generated GUI mockup.

Physical camera access was not exercised. Codecs and camera availability remain machine-dependent. Geometry/metrology are placeholders. Machine translations have not been certified by native technical reviewers. The original Kivy application and historical Python 2 examples were preserved rather than modernized or executed.

CI is configured for Python 3.10 and 3.12 on Linux; those remote jobs have not been observed until publication. The tested installation path is editable installation from the repository, which supplies the local learning assets and license alongside the application.

## Interface integration update

- Numerical/API/export/catalog suite: **48 passed**, including complete interface catalogs and preserved terminology corrections.
- The original browser workflow still passes.
- `verify_interface.cjs` passes for all 21 global interface languages. The tests confirm translated controls and blocks; unchanged equations, example code and graph parameters; and no frame advancement during language changes.
- The classroom opens in a modal iframe in the same browser page, synchronizes language and example programming language in both directions, retains exercise values, and closes through × or Escape. The full-lesson button selects the matching topic.
- The removable-card × is verified at the top-right, with successful removal and Undo. Required source/RGB cards remain fixed.
- Responsive checks pass at 390, 768 and 1512 pixels, including Arabic RTL and Japanese. The screenshots were refreshed from the working application.


## Expanded library and execution languages

- The numerical/API/export/catalog suite now contains **87 passing tests**, and the translation protection suite **6 passing tests** (93 total). The new checks cover all 28 registered kinds, analytic/OpenCV reference results, native Python/JavaScript parity, custom-code results, standalone exports in both runtimes, output shape/finite-value errors, worker timeout, import without execution, recipe dependencies and compatibility rejection.
- **All three browser suites passed**: original workflow, global interface/classroom, and the new `verify_library.cjs`. The latter exercises search and the grouped catalog, executable function insertion, disabled incompatible languages, code application in both runtimes, numerical output statistics, error recovery, saved library entries, reload, all five built-in example recipes, original source links, and 390/768/1512 pixel widths.
- Library: 28 block kinds (26 addable + 2 structural), five expression functions, five built-in recipes including four credited legacy adaptations, two repository presets, 37 original script references, saved blocks/projects, and a version-specific inspection catalog of OpenCV top-level functions/classes/constants. Reference entries are not misrepresented as executable adapters.
- Python and JavaScript custom code execute in separate local processes. Node.js is required for JavaScript; C/C++/Java execution stays disabled pending adapters. Four built-in operations have real JavaScript implementations, compared against Python with absolute tolerance 2e-7 on deterministic inputs. Standalone custom-block exports match the same-runtime engine bit for bit.
- Custom code is never executed just by configuration/import. Explicit execution is required for a new/changed custom graph. A timeout is not a security sandbox; user code has local-user permissions and arbitrary child-process/resource activity is not isolated.
- All 21 interface catalogs have 164 keys. Targeted corrections fix new action/technical labels; remaining machine drafts still require native technical review. Exact block formulas precede clearly labelled related background lessons.
- README screenshots come from the working local application. Physical cameras, remote CI and native C/C++/Java execution were not tested. Upload codecs remain machine-dependent. Hough output is pixel geometry, not calibrated metrology.
