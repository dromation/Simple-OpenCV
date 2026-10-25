# Browser checks

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
