"use strict";
const $ = (id) => document.getElementById(id),
  clone = (x) => structuredClone(x);
let state,
  blocks,
  token,
  selected = "algebra",
  running = false,
  valid = true,
  revision = 0,
  dirty = true,
  saved = "",
  queue = Promise.resolve(),
  history = [],
  future = [];
const limits = {
  wR: [-10, 10, 0.1],
  wG: [-10, 10, 0.1],
  wB: [-10, 10, 0.1],
  sigma: [0.1, 10, 0.1],
  margin: [0.001, 0.5, 0.001],
  threshold: [-10, 10, 0.01],
};
const labels = {
  expression: "Matematični izraz",
  input: "Vhodni kanal",
  output: "Izhodni kanal",
  sigma: "σ · standardni odklon",
  size: "Velikost jedra",
  margin: "Meja nasičenja",
  threshold: "Prag",
  kernel: "Jedro 3 × 3 (JSON)",
  wR: "wR",
  wG: "wG",
  wB: "wB",
};
function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function status(text, error = false) {
  $("status").textContent = text;
  document.body.classList.toggle("error", error);
}
async function api(path, data, raw = false) {
  const r = await fetch(
    path,
    data === undefined
      ? {}
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Studio-Token": token,
          },
          body: JSON.stringify(data),
        },
  );
  if (!r.ok) {
    const e = await r.json();
    throw Error(e.error || r.statusText);
  }
  return raw ? r.text() : r.json();
}
function serial(fn) {
  const p = queue.then(fn);
  queue = p.catch((e) => {
    running = false;
    $("run").textContent = "▶ Zaženi";
    status(e.message, true);
  });
  return p;
}
function channels(before = state.nodes.length) {
  const names = ["R", "G", "B", "A"];
  state.nodes.slice(0, before).forEach((n) => {
    if (n.kind === "difference") names.push("dR", "dG", "dB", "dA");
    if (n.params.output) names.push(n.params.output);
  });
  return names;
}
function mark() {
  dirty = JSON.stringify(state) !== saved;
  $("dirty").textContent = dirty ? "● Neshranjeno" : "✓ Shranjeno";
  $("undo").disabled = !history.length;
  $("redo").disabled = !future.length;
}
function remember() {
  history.push(clone(state));
  if (history.length > 60) history.shift();
  future = [];
}
function commit(change, redraw = true) {
  remember();
  change();
  mark();
  if (redraw) render();
  const snapshot = clone(state);
  valid = false;
  return serial(async () => {
    try {
      const r = await api("/api/config", snapshot);
      revision = r.revision;
      valid = true;
      status(
        "Spremembe uveljavljene · časovna zgodovina ponastavljena ob spremembi algoritma",
      );
      if (!running) await frame();
    } catch (e) {
      valid = false;
      throw e;
    }
  });
}
function selectOptions(select, items, value) {
  select.replaceChildren();
  items.forEach((item) => {
    const o = el("option", typeof item === "string" ? item : item.name);
    o.value = typeof item === "string" ? item : item.id;
    select.append(o);
  });
  select.value = value;
}
function download(text, name, type = "application/json") {
  const a = el("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
function slider(node, key, container) {
  const box = el("div", undefined, "param");
  const label = el("label", labels[key] || key),
    out = el("span", String(node.params[key]));
  label.append(out);
  const input = el("input");
  input.type = "range";
  [input.min, input.max, input.step] = limits[key];
  input.value = node.params[key];
  input.setAttribute("aria-label", `${blocks[node.kind].label} ${key}`);
  input.oninput = () => (out.textContent = input.value);
  input.onchange = () => commit(() => (node.params[key] = Number(input.value)));
  input.onclick = (e) => e.stopPropagation();
  box.append(label, input);
  container.append(box);
}
function renderLibrary() {
  const list = $("library");
  list.replaceChildren();
  const groups = [
    ["KANALI & MATEMATIKA", ["difference", "algebra", "confidence"]],
    [
      "FILTRI & ROBOVI",
      ["gaussian", "median", "kernel", "sobel", "scharr", "threshold"],
    ],
  ];
  for (const [name, kinds] of groups) {
    list.append(el("h3", name));
    for (const kind of kinds) {
      if (
        !`${kind} ${blocks[kind].label}`
          .toLowerCase()
          .includes($("search").value.toLowerCase())
      )
        continue;
      const b = el("button", undefined, "library-card");
      b.dataset.kind = kind;
      b.draggable = true;
      b.append(
        el("b", `＋ ${blocks[kind].label}`),
        el(
          "small",
          kind === "algebra"
            ? "f(R, G, B, ΔR, …)"
            : kind === "kernel"
              ? "3 × 3 · lastni koeficienti"
              : `OpenCV / ${kind}`,
        ),
      );
      b.onclick = () => add(kind);
      b.ondragstart = (e) =>
        e.dataTransfer.setData("text/plain", JSON.stringify({ kind }));
      list.append(b);
    }
  }
}
function add(kind, index = state.nodes.length) {
  if (kind === "difference" && state.nodes.some((n) => n.kind === kind)) {
    status("Blok razlike je že na platnu. Izberi ga za razlago.");
    return;
  }
  commit(() => {
    index = Math.max(2, index);
    const p = clone(blocks[kind].params),
      names = channels(index);
    if (p.input && !names.includes(p.input)) p.input = names.at(-1);
    if (p.expression && !names.includes("dR"))
      p.expression = "wR*R + wG*G + wB*B";
    if (p.output) {
      const base = p.output;
      let n = 2;
      while (channels().includes(p.output)) p.output = base + n++;
    }
    const node = {
      id: kind + "_" + Date.now().toString(36),
      kind,
      enabled: true,
      params: p,
    };
    state.nodes.splice(index, 0, node);
    selected = node.id;
  });
}
function reorder(id, index) {
  const from = state.nodes.findIndex((n) => n.id === id);
  if (from < 2) return;
  commit(() => {
    const [node] = state.nodes.splice(from, 1);
    state.nodes.splice(
      Math.max(2, Math.min(index, state.nodes.length)),
      0,
      node,
    );
  });
}
function renderGraph() {
  const graph = $("graph");
  graph.replaceChildren();
  state.nodes.forEach((node, index) => {
    const card = el(
      "article",
      undefined,
      `node${node.id === selected ? " selected" : ""}${node.enabled ? "" : " bypass"}`,
    );
    card.dataset.id = node.id;
    card.draggable = index >= 2;
    card.tabIndex = 0;
    card.onclick = () => {
      selected = node.id;
      renderGraph();
      renderInspector();
    };
    card.onkeydown = (e) => {
      if (e.key === "Enter") {
        selected = node.id;
        render();
      }
    };
    card.ondragstart = (e) => {
      if (e.target !== card) {
        e.preventDefault();
        return;
      }
      e.dataTransfer.setData("text/plain", JSON.stringify({ id: node.id }));
    };
    card.ondragover = (e) => {
      e.preventDefault();
      card.classList.add("drop-target");
    };
    card.ondragleave = () => card.classList.remove("drop-target");
    card.ondrop = (e) => {
      e.preventDefault();
      e.stopPropagation();
      drop(e, index);
    };
    const head = el("div", undefined, "node-head");
    head.append(
      el("span", String(index + 1).padStart(2, "0"), "node-number"),
      el("h3", blocks[node.kind].label),
    );
    card.append(head);
    if (node.params.expression)
      card.append(el("div", node.params.expression, "expression"));
    if (node.kind === "source")
      card.append(
        el(
          "div",
          `${state.source.type} · ${state.source.type === "camera" ? "kamera " + state.source.camera : "lokalni vir"}`,
          "description",
        ),
      );
    else if (node.kind === "channels")
      card.append(
        el(
          "div",
          "R  ·  G  ·  B  ·  A\nNormalizacija [0, 1] + ocena nasičenja",
          "description",
        ),
      );
    else if (node.kind === "difference")
      card.append(
        el("div", "ΔC = C(t) − C(t−1)\nΔR · ΔG · ΔB · ΔA", "description"),
      );
    else if (node.params.input)
      card.append(
        el(
          "div",
          `${node.params.input} → ${node.params.output}${node.params.size ? " · " + node.params.size + " × " + node.params.size : ""}`,
          "description",
        ),
      );
    for (const k of ["wR", "wG", "wB", "sigma", "margin", "threshold"])
      if (k in node.params) slider(node, k, card);
    if (index >= 2) {
      const controls = el("div", undefined, "node-controls");
      for (const [text, title, fn] of [
        ["↑", "Move earlier", () => reorder(node.id, index - 1)],
        ["↓", "Move later", () => reorder(node.id, index + 1)],
        [
          "×",
          "Remove block",
          () =>
            commit(() => {
              state.nodes.splice(index, 1);
              selected = state.nodes[Math.max(0, index - 1)].id;
              for (const k of ["signal", "result"])
                if (!channels().includes(state.view[k])) state.view[k] = "R";
            }),
        ],
      ]) {
        const b = el("button", text);
        b.title = title;
        b.onclick = (e) => {
          e.stopPropagation();
          fn();
        };
        controls.append(b);
      }
      card.append(controls);
    }
    graph.append(card);
  });
}
function drop(e, index) {
  try {
    const data = JSON.parse(e.dataTransfer.getData("text/plain"));
    if (data.kind && blocks[data.kind]) add(data.kind, index);
    else if (data.id) reorder(data.id, index);
  } catch {}
}
$("graph").ondragover = (e) => e.preventDefault();
$("graph").ondrop = (e) => {
  e.preventDefault();
  drop(e, state.nodes.length);
};
function field(title, input) {
  const label = el("label", title, "field");
  label.append(input);
  $("parameters").append(label);
}
function renderInspector() {
  const node = state.nodes.find((n) => n.id === selected) || state.nodes[0];
  selected = node.id;
  $("selectedTitle").textContent = blocks[node.kind].label;
  $("parameters").replaceChildren();
  if (node.kind === "source") {
    const source = el("select");
    selectOptions(
      source,
      [
        { id: "synthetic", name: "Sintetični demo" },
        { id: "camera", name: "Kamera" },
        { id: "image", name: "Slika …" },
        { id: "video", name: "Video …" },
      ],
      state.source.type,
    );
    source.onchange = () => {
      if (["image", "video"].includes(source.value)) {
        $("media").click();
        source.value = state.source.type;
      } else commit(() => (state.source.type = source.value));
    };
    field("Vir zajema", source);
    if (state.source.type === "camera") {
      const cam = el("input");
      cam.type = "number";
      cam.min = 0;
      cam.max = 16;
      cam.value = state.source.camera;
      cam.onchange = () =>
        commit(() => (state.source.camera = Number(cam.value)));
      field("Indeks kamere", cam);
    }
    const upload = el("button", "Izberi sliko ali video …");
    upload.onclick = () => $("media").click();
    $("parameters").append(upload);
  } else if (["channels", "difference"].includes(node.kind)) {
    $("parameters").append(
      el(
        "p",
        node.kind === "difference"
          ? "Prva sličica po spremembi algoritma ima ničelno razliko."
          : "A je izpeljana ocena nasičenja, ne meritev prosojnosti ali verjetnost.",
      ),
    );
  }
  for (const [key, value] of Object.entries(node.params)) {
    let input;
    if (key === "input" || key === "size") {
      input = el("select");
      selectOptions(
        input,
        key === "input"
          ? channels(state.nodes.indexOf(node))
          : (node.kind === "median"
              ? [3, 5]
              : node.kind === "sobel"
                ? [3, 5, 7]
                : [3, 5, 7, 9, 11, 13, 15]
            ).map(String),
        String(value),
      );
    } else if (key === "expression" || key === "kernel") {
      input = el("textarea");
      input.rows = key === "kernel" ? 4 : 3;
      input.value = key === "kernel" ? JSON.stringify(value) : value;
    } else {
      input = el("input");
      input.value = value;
      if (typeof value === "number") {
        input.type = "number";
        input.step = "any";
        if (limits[key]) {
          input.min = limits[key][0];
          input.max = key === "threshold" ? 10 : limits[key][1];
          if (key === "threshold") input.min = -10;
        }
      }
    }
    input.dataset.parameter = key;
    input.onchange = () => {
      try {
        const v =
          key === "kernel"
            ? JSON.parse(input.value)
            : typeof value === "number"
              ? Number(input.value)
              : input.value;
        commit(() => (node.params[key] = v));
      } catch (e) {
        status(e.message, true);
      }
    };
    field(labels[key] || key, input);
  }
  if ("input" in node.params) {
    const enabled = el("input");
    enabled.type = "checkbox";
    enabled.checked = node.enabled;
    enabled.onchange = () => commit(() => (node.enabled = enabled.checked));
    field("Operacija vključena (izklop = prehod vhoda)", enabled);
  }
  renderLesson(node);
}
function renderLesson(node) {
  const lesson = window.LESSONS?.find((l) => l.id === blocks[node.kind].lesson);
  const area = $("lesson");
  area.replaceChildren();
  if (!lesson) {
    area.append(
      el("p", "Učni paket ni nameščen. Odpri dokumentacijo v repozitoriju."),
    );
    return;
  }
  const locale = state.view.locale,
    cat = window.TRANSLATIONS?.catalogs?.[locale];
  const lang = window.TRANSLATIONS?.languages.find((l) => l.id === locale);
  area.dir = lang?.dir || "ltr";
  area.lang = lang?.tag || "en";
  const translated = (key) =>
    cat?.strings?.[`lesson.${lesson.id}.${key}`] ||
    lesson[key]?.[locale] ||
    lesson[key]?.en ||
    "";
  if (!["sl", "en"].includes(locale))
    area.append(
      el(
        "p",
        "Machine translation · strojni osnutek. Verify with the English original.",
        "draft",
      ),
    );
  area.append(
    el("p", translated("summary")),
    el("div", lesson.formula, "formula"),
    el("p", translated("variables")),
    el("p", translated("example")),
    el("p", translated("caution")),
  );
  const detail = el("details");
  detail.open = !["sl", "en"].includes(locale);
  detail.dir = "ltr";
  detail.append(
    el("summary", "English original"),
    el("p", lesson.summary.en),
    el("p", lesson.variables.en),
    el("p", lesson.caution.en),
  );
  area.append(detail);
  const link = el("a", "Celotna razlaga / Full lesson ↗");
  link.href = "/manuals/learning/index.html#" + lesson.id;
  link.target = "_blank";
  link.rel = "noopener";
  area.append(link);
  $("example").textContent =
    lesson[state.view.codeLanguage] || "Example unavailable";
}
function render() {
  $("name").value = state.name;
  renderLibrary();
  renderGraph();
  renderInspector();
  for (const key of ["signal", "result"])
    selectOptions($(key), channels(), state.view[key]);
  $("gain").value = state.view.gain;
  $("signed").checked = state.view.signed;
  $("locale").value = state.view.locale;
  $("codeLanguage").value = state.view.codeLanguage;
  mark();
}
async function frame() {
  if (!valid) return;
  const data = await api("/api/frame", {});
  if (data.ended) {
    running = false;
    $("run").textContent = "▶ Zaženi";
    status(data.message);
    return;
  }
  if (data.revision !== revision) return;
  for (const [key, id] of [
    ["camera", "camera"],
    ["signal", "signalImage"],
    ["result", "resultImage"],
  ])
    $(id).src = data.images[key];
  for (const key of ["signal", "result"]) {
    const s = data.stats[state.view[key]];
    if (s)
      $(key + "Stats").textContent =
        `min ${s.min.toFixed(4)} · max ${s.max.toFixed(4)} · μ ${s.mean.toFixed(4)}`;
  }
  $("dimensions").textContent = data.size.join(" × ");
  status(
    `Sličica ${data.frame} · ${data.processingMs} ms · ${data.ready ? "Δ zgodovina pripravljena" : "Prva sličica: Δ = 0"}${data.size[0] !== data.originalSize[0] ? " · predogled pomanjšan na največ 960 px" : ""}`,
  );
}
async function loop() {
  if (!running) return;
  try {
    await serial(frame);
  } catch {}
  if (running) setTimeout(loop, 70);
}
$("run").onclick = () => {
  if (!valid) {
    status("Najprej popravi označeno konfiguracijo.", true);
    return;
  }
  running = !running;
  $("run").textContent = running ? "Ⅱ Premor" : "▶ Zaženi";
  if (running) loop();
  else if (state.source.type === "camera") serial(() => api("/api/stop", {}));
};
$("step").onclick = () => serial(frame);
$("name").onchange = () => commit(() => (state.name = $("name").value), false);
$("search").oninput = renderLibrary;
for (const key of ["signal", "result", "locale", "codeLanguage"])
  $(key).onchange = () => commit(() => (state.view[key] = $(key).value));
$("gain").onchange = () =>
  commit(() => (state.view.gain = Number($("gain").value)));
$("signed").onchange = () =>
  commit(() => (state.view.signed = $("signed").checked));
for (const [id, from, to] of [
  ["undo", () => history, () => future],
  ["redo", () => future, () => history],
])
  $(id).onclick = () => {
    if (!from().length) return;
    to().push(clone(state));
    state = from().pop();
    render();
    const snapshot = clone(state);
    valid = false;
    serial(async () => {
      const r = await api("/api/config", snapshot);
      revision = r.revision;
      valid = true;
      await frame();
    });
  };
$("save").onclick = () =>
  serial(async () => {
    if (!valid) throw Error("Popravi konfiguracijo pred shranjevanjem.");
    const record = await api("/api/save", state);
    saved = JSON.stringify(state);
    mark();
    download(JSON.stringify(record.state, null, 2), "simplemotocam-state.json");
    status("Stanje shranjeno lokalno in preneseno kot JSON.");
  });
$("export").onclick = () =>
  serial(async () => {
    if (!valid) throw Error("Popravi konfiguracijo pred izvozom.");
    download(
      await api("/api/export", state, true),
      "simplemotocam_algorithm.py",
      "text/x-python",
    );
    status("Samostojni Python algoritem izvožen · zahteva NumPy in OpenCV.");
  });
async function load(newState) {
  running = false;
  $("run").textContent = "▶ Zaženi";
  const r = await api("/api/config", newState);
  remember();
  state = r.state;
  revision = r.revision;
  valid = true;
  saved = JSON.stringify(state);
  render();
  $("projects").close();
  if (state.source.type === "synthetic" || state.source.type === "image")
    await frame();
}
$("open").onclick = () =>
  serial(async () => {
    const projects = await api("/api/projects");
    $("projectList").replaceChildren();
    for (const item of projects) {
      const b = el(
        "button",
        `${item.name} · ${new Date(item.savedAt).toLocaleString()}`,
      );
      b.onclick = () => {
        if (
          dirty &&
          !confirm("Odpri projekt in zapusti neshranjene spremembe?")
        )
          return;
        serial(async () =>
          load(
            (await api("/api/projects/" + encodeURIComponent(item.id))).state,
          ),
        );
      };
      $("projectList").append(b);
    }
    if (!projects.length)
      $("projectList").append(
        el(
          "p",
          "Ni shranjenih projektov. Uvozi JSON ali shrani trenutno stanje.",
        ),
      );
    $("projects").showModal();
  });
$("closeProjects").onclick = () => $("projects").close();
$("import").onchange = async () => {
  const file = $("import").files[0];
  if (!file) return;
  if (dirty && !confirm("Uvozi projekt in zapusti neshranjene spremembe?"))
    return;
  serial(async () => {
    if (file.size > 262144) throw Error("JSON je prevelik (največ 256 KB).");
    const data = JSON.parse(await file.text());
    await load(data.state || data);
  });
  $("import").value = "";
};
$("media").onchange = () => {
  const file = $("media").files[0];
  if (!file) return;
  serial(async () => {
    if (file.size > 100 * 1024 * 1024)
      throw Error("Največja velikost vira je 100 MB.");
    const r = await fetch("/api/upload", {
      method: "POST",
      headers: {
        "X-Studio-Token": token,
        "X-File-Extension": "." + file.name.split(".").pop().toLowerCase(),
      },
      body: file,
    });
    const data = await r.json();
    if (!r.ok) throw Error(data.error);
    remember();
    state.source = { ...state.source, type: data.type, asset: data.asset };
    const config = await api("/api/config", state);
    revision = config.revision;
    valid = true;
    render();
    await frame();
  });
  $("media").value = "";
};
$("guide").onclick = () =>
  window.open("/manuals/learning/index.html", "_blank", "noopener");
window.addEventListener("beforeunload", (e) => {
  if (dirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});
async function start() {
  const data = await api("/api/bootstrap");
  ({ state, blocks, token, revision } = data);
  selectOptions(
    $("locale"),
    window.TRANSLATIONS?.languages || [
      { id: "sl", name: "Slovenščina" },
      { id: "en", name: "English" },
    ],
    state.view.locale,
  );
  render();
  await frame();
  await frame();
}
start().catch((e) => status(e.message, true));
