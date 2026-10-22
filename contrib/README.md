# Experimental contributions

Open a preset from the studio with **Odpri → Uvozi JSON**. These JSON configurations use the same validation and mathematical engine as the main application.

- `presets/color-contrast.json`: signed red–green contrast, Gaussian smoothing and Sobel magnitude. Works on a single still image.
- `presets/temporal-motion.json`: per-channel differences and weighted motion signal. Run at least two frames after changing an algorithm parameter.

To create your own block without modifying Python, use **Algebra kanalov** (safe mathematical expressions) or **Lastno jedro** (an editable 3×3 correlation kernel). Expressions support `+ - * / **`, channel names, `wR/wG/wB`, `abs`, `sqrt`, `minimum`, `maximum` and `clip`. Functions operate pixel by pixel. Nonfinite results stop processing with an error instead of silently corrupting a frame.

To implement a new operation in Python, follow [CONTRIBUTING.md](../CONTRIBUTING.md). Geometry and metrology are extension points; they do not yet provide calibrated measurement tools. Never label pixel distances as physical lengths without calibration.
