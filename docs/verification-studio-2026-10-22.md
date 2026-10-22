# Studio verification — 2026-10-22

Verified locally on Windows, Python 3.10.11, NumPy 2.2.6, OpenCV 4.14.0 and Chrome driven by Playwright 1.62.1.

- `python -m pytest`: **47 passed**. Covers core channels/operators, signed differences, first-frame handling, safe expression rejection, error-history isolation, custom kernels, confidence, bypass/order validation, state persistence, HTTP token/origin checks, image/video sources and standalone export.
- `python -m pytest tools/doc_translate/test_translate.py`: **5 passed**. Translation protection checks.
- `tools/browser-tests/verify.cjs`: **passed**. Actual drag insertion, reorder controls, invalid formula recovery through Undo, JSON save/load equality, executing the downloaded Python export, image upload, all 21 explanation languages, Arabic RTL, all four code-example languages, no external frontend requests, no JavaScript errors and no horizontal overflow at 390/768/1512 pixel viewport widths.
- Standalone export matches every numerical channel of the studio engine on five deterministic synthetic frames, bit for bit. This comparison uses identical input dimensions.
- README screenshots are captures of the running application with the synthetic source, not the earlier generated GUI mockup.

Physical camera access was not exercised. Codecs and camera availability remain machine-dependent. Geometry/metrology are placeholders. Machine translations have not been certified by native technical reviewers. The original Kivy application and historical Python 2 examples were preserved rather than modernized or executed.

CI is configured for Python 3.10 and 3.12 on Linux; those remote jobs have not been observed until publication. The tested installation path is editable installation from the repository, which supplies the local learning assets and license alongside the application.
