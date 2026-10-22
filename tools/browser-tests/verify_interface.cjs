const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const url = process.env.STUDIO_TEST_URL || "http://127.0.0.1:8766";
(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_PATH
      ? { executablePath: process.env.CHROME_PATH }
      : {}),
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1512, height: 1050 },
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("dialog", (d) => d.accept());
    const bootstrap = await (
      await page.request.get(url + "/api/bootstrap")
    ).json();
    const initial = JSON.parse(
      fs.readFileSync(
        path.join(root, "contrib/presets/temporal-motion.json"),
        "utf8",
      ),
    );
    await page.request.post(url + "/api/config", {
      headers: { "X-Studio-Token": bootstrap.token },
      data: initial,
    });
    await page.goto(url);
    await page.waitForFunction(
      () => document.querySelector("#status").dataset.frame,
    );
    const change = async (action) => {
      const response = page.waitForResponse(
        (r) => r.url() === url + "/api/config",
      );
      await action();
      assert((await response).ok());
    };
    const getState = async () =>
      (await (await page.request.get(url + "/api/bootstrap")).json()).state;
    const setLocale = async (locale) => {
      if ((await page.locator("#locale").inputValue()) !== locale)
        await change(() => page.selectOption("#locale", locale));
    };
    const code = await page.locator("#example").textContent(),
      formula = await page.locator(".formula").textContent();
    const frameNumber = await page
      .locator("#status")
      .getAttribute("data-frame");
    const locales = await page
      .locator("#locale option")
      .evaluateAll((es) => es.map((e) => e.value));
    for (const locale of locales) {
      await setLocale(locale);
      const strings = await page.evaluate(
        (l) => window.STUDIO_I18N[l].strings,
        locale,
      );
      for (const id of ["save", "open", "export", "guide"])
        assert.equal(await page.locator("#" + id).textContent(), strings[id]);
      assert.equal(
        await page.locator("#selectedTitle").textContent(),
        strings.algebraBlock,
      );
      assert.equal(await page.locator("#example").textContent(), code);
      assert.equal(await page.locator(".formula").textContent(), formula);
      assert.equal(
        await page.locator("#status").getAttribute("data-frame"),
        frameNumber,
        "language must not advance source",
      );
      assert.deepEqual((await getState()).nodes, initial.nodes);
      assert.equal(
        await page.locator("html").getAttribute("dir"),
        locale === "ar" ? "rtl" : "ltr",
      );
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "overflow: " + locale,
      );
    }
    await setLocale("en");
    await page.locator("#guide").click();
    const iframe = page.frameLocator("#classroomFrame");
    await iframe.locator("#locale").waitFor();
    await page.waitForFunction(
      () =>
        document
          .querySelector("#classroomFrame")
          .contentDocument.querySelector("#locale")?.value === "en",
    );
    assert.equal(page.context().pages().length, 1);
    await change(() => iframe.locator("#locale").selectOption("de"));
    assert.equal(await page.locator("#locale").inputValue(), "de");
    assert.equal(
      await page.locator("#save").textContent(),
      "Zustand speichern",
    );
    await change(() => iframe.locator("#program").selectOption("cpp"));
    assert.equal(await page.locator("#codeLanguage").inputValue(), "cpp");
    await iframe.locator("#param-0").fill("123");
    await iframe.locator("#param-0").dispatchEvent("input");
    await page.locator("#closeClassroom").click();
    assert.equal(await page.locator("#classroom").isVisible(), false);
    await page.locator("#libraryGuide").click();
    assert.equal(await iframe.locator("#param-0").inputValue(), "123");
    await iframe.locator("#locale").focus();
    await page.keyboard.press("Escape");
    await page.waitForFunction(
      () => !document.querySelector("#classroom").open,
    );
    await page.locator(".full-lesson").click();
    await page.waitForFunction(() =>
      document
        .querySelector("#classroomFrame")
        .contentDocument.querySelector('#topics [aria-current="page"]')
        ?.textContent.startsWith("03"),
    );
    assert.equal(page.context().pages().length, 1);
    fs.mkdirSync(path.join(root, "work/browser-checks"), { recursive: true });
    await page.screenshot({
      path: path.join(root, "work/browser-checks/classroom-overlay.png"),
    });
    await page.locator("#closeClassroom").click();
    await change(() => page.locator('[data-kind="confidence"]').click());
    const added = (await getState()).nodes.at(-1).id;
    const card = page.locator(`[data-id="${added}"]`),
      close = card.locator(".node-close");
    await close.scrollIntoViewIfNeeded();
    const c = await card.boundingBox(),
      x = await close.boundingBox();
    assert(
      x.y - c.y < 15 && c.x + c.width - x.x - x.width < 15,
      "X must be at top right",
    );
    assert.equal(await card.locator(".node-controls .node-close").count(), 0);
    assert.equal(
      await page
        .locator(
          '[data-id="source"] .node-close, [data-id="channels"] .node-close',
        )
        .count(),
      0,
    );
    await change(() => close.click());
    assert(!(await getState()).nodes.some((n) => n.id === added));
    await change(() => page.locator("#undo").click());
    assert((await getState()).nodes.some((n) => n.id === added));
    for (const width of [390, 768, 1512]) {
      await page.setViewportSize({ width, height: 900 });
      for (const locale of ["en", "ar", "ja"]) {
        await setLocale(locale);
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
          ),
          false,
          `overflow ${width}/${locale}`,
        );
        await page.locator("#guide").click();
        const box = await page.locator("#classroom").boundingBox();
        assert(box.x >= 0 && box.x + box.width <= width + 1);
        await page.locator("#closeClassroom").click();
      }
    }
    await setLocale("sl");
    await page.reload();
    await page.waitForFunction(
      () => document.querySelector("#status").dataset.frame,
    );
    assert.equal(await page.locator("#locale").inputValue(), "sl");
    assert.deepEqual(errors, []);
    console.log(
      JSON.stringify({
        passed: true,
        interfaceLanguages: locales.length,
        overlay:
          "same window, synchronized language/code, X and Escape, state retained",
        cards: "top-right X, remove and undo",
        viewports: 3,
      }),
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
