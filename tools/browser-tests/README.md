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
