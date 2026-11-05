# Browser checks

For the static addon-domain edition, build `python tools/package_static.py`, then
serve `dist/` with `python -m http.server 8780 --bind 127.0.0.1 --directory dist`.
Run `npm run test:static`. For numerical parity, first run
`python tools/browser-tests/static_reference.py` from the project root, then
`npm run test:static:numeric` here. These use only a plain static file server,
check that no `/api` requests occur, verify 2.4 as the default and both engine
choices, and compare 136 cases (24 mathematical/vision blocks, extra parameter
sets, noise and structured detection scenes) to genuine native 2.4 / current
references. Build the native 2.4 worker before generating fixtures. Camera tests use a fake browser
device; they do not access the user's camera. Storage is a fresh test profile.

Use a **disposable** server session: this test edits its state and saves synthetic test projects.

```sh
python -m simplemotocam.studio --no-browser --port 8766 --storage work/browser-test-session
```

In a second terminal, install the optional test dependency and run:

```sh
cd tools/browser-tests
npm install
npx playwright install chromium
npm test
```

`STUDIO_TEST_URL`, `PYTHON`, and `CHROME_PATH` can override the server URL, Python executable and browser executable. The normal application does not need Node or Playwright. Results and generated media stay in ignored `work/browser-checks/`.

Run `npm run test:interface` against the same disposable server to check all 21 application languages, unchanged formulas/code/algorithm state, synchronized classroom overlay, Escape/close behavior, top-right block removal and responsive layouts.

Run `npm run test:library` for catalog/custom-code checks. With the optional native OpenCV 2.4 worker installed, run `npm run test:backends` to verify actual 2.4 processing, saved profiles, compatibility and failed-switch preservation. All suites mutate the disposable session.

Start the disposable session with its default primary OpenCV 2.4 engine and run `npm run test:sequences` before suites that replace its graph. This checks all six classroom recipes, synthetic scenes, source references, custom native code, language sync and three widths.

`npm run test:empty-block` checks arbitrary language selection, separate persistent drafts, project save/reload, unavailable-runtime bypass, actual Python results, incomplete-code drafts and three viewport widths.

`npm run test:compiled` requires the native OpenCV 2.4 worker, C/C++ compilers and a JDK. It compiles/runs all three languages through the editor, checks actual numerical results, compiler diagnostics and recovery, saves each language draft and reloads the project.
