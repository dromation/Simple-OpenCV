// Run against a disposable studio session; never against a user's active project.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const root = path.resolve(__dirname, "../..");
const url = process.env.STUDIO_TEST_URL || "http://127.0.0.1:8766";
const output = path.join(root, "work/browser-checks");
fs.mkdirSync(output, { recursive: true });
const python =
  process.env.PYTHON ||
  (process.platform === "win32"
    ? path.join(root, ".venv/Scripts/python.exe")
    : path.join(root, ".venv/bin/python"));
(async () => {
  const browser = await chromium.launch(
    process.env.CHROME_PATH
      ? { executablePath: process.env.CHROME_PATH, headless: true }
      : { headless: true },
  );
  try {
    const page = await browser.newPage({
        viewport: { width: 1512, height: 1050 },
      }),
      errors = [],
      external = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("dialog", (d) => d.accept());
    page.on("request", (r) => {
      if (
        !r.url().startsWith(url) &&
        !r.url().startsWith("data:") &&
        !r.url().startsWith("blob:")
      )
        external.push(r.url());
    });
    const bootstrap = await (
      await page.request.get(url + "/api/bootstrap")
    ).json();
    const initial = JSON.parse(
      fs.readFileSync(
        path.join(root, "contrib/presets/temporal-motion.json"),
        "utf8",
      ),
    );
    assert(
      (
        await page.request.post(url + "/api/config", {
          headers: { "X-Studio-Token": bootstrap.token },
          data: initial,
        })
      ).ok(),
    );
    const state = async () =>
      (await (await page.request.get(url + "/api/bootstrap")).json()).state;
    const settled = async () => {
      await page.waitForFunction(
        () =>
          !document.body.classList.contains("error") &&
          Boolean(document.querySelector("#status").dataset.frame),
      );
    };
    const edit = async (key, value, ok = true) => {
      const response = page.waitForResponse(
        (r) =>
          r.url() === url + "/api/config" && r.request().method() === "POST",
      );
      const input = page.locator(`[data-parameter="${key}"]`);
      await input.fill(value);
      await input.press("Tab");
      assert.equal((await response).ok(), ok);
      if (ok) await settled();
    };
    await page.goto(url);
    await settled();
    await page.locator('[data-id="algebra"] .node-head').click();
    await edit("expression", "R - G");
    await edit("wR", "2.5");
    assert.equal((await state()).nodes[3].params.expression, "R - G");
    await edit("expression", "1 / (R-R)", false);
    await page.waitForFunction(() => document.body.classList.contains("error"));
    assert.equal(
      (await state()).nodes[3].params.expression,
      "R - G",
      "invalid draft must not replace valid state",
    );
    await page.locator("#undo").click();
    await settled();
    const graphBox = await page.locator("#graph").boundingBox();
    await page
      .locator('[data-kind="threshold"]')
      .dragTo(page.locator("#graph"), {
        targetPosition: { x: 2, y: graphBox.height - 2 },
      });
    await page.waitForFunction(
      () => document.querySelectorAll(".node").length === 7,
    );
    await settled();
    assert.equal((await state()).nodes.at(-1).kind, "threshold");
    await page.selectOption("#result", "mask");
    await settled();
    const snapshot = await state();
    const save = page.waitForEvent("download");
    await page.locator("#save").click();
    const download = await save;
    const jsonPath = path.join(output, "state.json");
    await download.saveAs(jsonPath);
    assert.deepEqual(JSON.parse(fs.readFileSync(jsonPath, "utf8")), snapshot);
    await page.locator("#open").click();
    await page.locator("#projectList button").first().click();
    await settled();
    assert.deepEqual(await state(), snapshot);
    const exp = page.waitForEvent("download");
    await page.locator("#export").click();
    const exported = path.join(output, "algorithm.py");
    await (await exp).saveAs(exported);
    assert.equal(
      JSON.parse(
        execFileSync(python, [exported, "--frames", "5"], { encoding: "utf8" }),
      ).frames,
      5,
    );
    const locales = await page
      .locator("#locale option")
      .evaluateAll((es) => es.map((e) => e.value));
    assert.equal(locales.length, 21);
    for (const locale of locales) {
      await page.selectOption("#locale", locale);
      await settled();
      assert(await page.locator("#lesson p").first().textContent());
      if (locale === "ar")
        assert.equal(await page.locator("#lesson").getAttribute("dir"), "rtl");
    }
    for (const language of ["python", "cpp", "c", "java"]) {
      await page.selectOption("#codeLanguage", language);
      await settled();
      assert((await page.locator("#example").textContent()).length > 20);
    }
    await page.locator('[data-id="source"] .node-head').click();
    // Small deterministic input, generated locally with the project engine.
    const media = path.join(output, "source.png");
    execFileSync(python, [
      "-c",
      "import cv2; from simplemotocam.studio_engine import demo_frame; import sys; cv2.imwrite(sys.argv[1],demo_frame(2))",
      media,
    ]);
    await page.locator("#media").setInputFiles(media);
    await page.waitForFunction(
      () =>
        document.querySelector('[data-id="source"]').dataset.sourceType ===
        "image",
    );
    await settled();
    assert.equal((await state()).source.type, "image");
    // Unconnected appended blocks can be reordered without altering dependencies.
    await page.locator('[data-kind="confidence"]').click();
    await settled();
    const added = (await state()).nodes.at(-1).id;
    await page
      .locator(`[data-id="${added}"] button[data-action="earlier"]`)
      .click();
    await settled();
    assert.equal((await state()).nodes.at(-2).id, added);
    for (const width of [390, 768, 1512]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        `overflow at ${width}`,
      );
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    console.log(
      JSON.stringify(
        {
          passed: true,
          explanationLanguages: locales.length,
          exampleLanguages: 4,
          viewports: 3,
          checks:
            "drag, reorder, invalid math, undo, save/load, Python export, image upload, offline requests",
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
