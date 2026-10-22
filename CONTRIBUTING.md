# Contributing to SimpleMotocam

Build small, inspectable computer-vision experiments. A block should make its mathematics, inputs, outputs and limitations clear.

## Development

Use Python 3.10 or newer. From this repository:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
python -m simplemotocam.studio
```

The current studio uses NumPy and OpenCV 4. The OpenCV 2.4 source/manuals are historical learning references, not runtime dependencies. Do not install Python 2 dependencies into this environment.

## Adding an algorithm

1. Describe its input channels, numeric range, border policy and output units. Keep float32 signed results until display mapping.
2. Add its descriptor and parameter constraints to `src/simplemotocam/studio_engine.py`, then implement its operation in `StudioPipeline.process`. The exported standalone script embeds this same engine.
3. Add a meaningful mathematical test in `tests_core/`, such as an impulse, ramp, constant image or signed difference. Include invalid parameters and edge cases where relevant.
4. Expose controls in `studio_ui/app.js` and add a lesson or link to an existing one. Test editing, bypass, save/load and export in the browser.
5. Submit a focused pull request with a screenshot for UI changes and the checks you ran.

The studio is an **ordered dataflow**, not an arbitrary graph scheduler. A block can read any previously produced channel. Reordering never silently rewires inputs: invalid dependencies are reported. `contrib/` contains starter configurations and extension guidance. The restricted algebra parser stays separate from explicitly run trusted custom-code blocks. Importing a custom-code project must never execute its code.

## Translation and mathematical review

English and Slovenian lessons are authored text. The other 19 languages are machine drafts. Corrections belong in `tools/doc_translate/corrections/<language>.json`; regenerate with the documented local translation workflow. Keep equations, variable names and code intact. Have a fluent technical reviewer check translations before describing them as reviewed.

## Repository boundaries

Preserve the original Kivy application and historical examples. Avoid mass formatting or changing their licenses. Do not commit `.venv`, translation models, `.motocam` recordings/uploads, credentials or external source snapshots. Synthetic demo images are suitable for screenshots.

New contributions are submitted under the project MIT license. Credit external algorithms and retain their original notices; do not copy code with unknown or incompatible licensing. Participation follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).


## Execution backends and library entries

The library is derived from the executable `KINDS` registry plus `studio_catalog.py` recipes and references. Add authored English/Slovenian labels and regenerate the other interface catalogs with `Update-Studio-Translations.cmd`. Prefer exact mathematical formulas in descriptors and clearly label related background lessons. References with incompatible input/output contracts must remain reference entries.

Runtime compatibility is declared in `studio_runtime.py` (contract version 1). A new adapter needs an availability check, explicit supported block kinds, worker implementation, finite H × W output validation and standalone-export parity tests. The UI must disable unavailable/incompatible choices. Native compiler installation alone is not sufficient. Preserve legacy state files where an absent runtime means Python.

Run `tools/browser-tests/verify_library.cjs` against a disposable studio session for code editing, language switching, saved recipes and numeric output checks. Also run the original workflow and global-language/classroom tests. See [the runtime extension guide](docs/STUDIO.md#updating-execution-backends).
