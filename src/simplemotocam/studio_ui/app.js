"use strict";
const $ = (id) => document.getElementById(id),
  clone = (x) => structuredClone(x);
let state,
  blocks,
  catalog,
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
function t(key) {
  return (
    window.STUDIO_I18N?.[state?.view.locale]?.strings?.[key] ||
    window.STUDIO_I18N?.en?.strings?.[key] ||
    key
  );
}
function blockLabel(kind) {
  return t(kind === "source" ? "source" : kind + "Block");
}
function paramLabel(key) {
  return ["wR", "wG", "wB"].includes(key) ? key : t(key);
}
function translateInterface() {
  const lang = window.TRANSLATIONS.languages.find(
    (l) => l.id === state.view.locale,
  ) || { tag: "en", dir: "ltr" };
  document.documentElement.lang = lang.tag;
  document.documentElement.dir = lang.dir;
  for (const [attribute, target] of [
    ["data-i18n", null],
    ["data-i18n-placeholder", "placeholder"],
    ["data-i18n-aria", "aria-label"],
    ["data-i18n-alt", "alt"],
    ["data-i18n-title", "title"],
  ]) {
    document.querySelectorAll("[" + attribute + "]").forEach((e) => {
      const text = t(e.getAttribute(attribute));
      if (target) e.setAttribute(target, text);
      else e.textContent = text;
    });
  }
  $("run").textContent =
    (running ? "Ⅱ " : "▶ ") + t(running ? "pause" : "run");
  $("interfaceDraft").hidden = ["sl", "en"].includes(state.view.locale);
  $("closeCatalog").setAttribute("aria-label", t("closeBlock"));
  syncClassroom();
}

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
    $("run").textContent = "▶ " + t("run");
    status(t("error") + ": " + e.message, true);
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
  dirty = JSON.stringify(state) !== saved || pendingCode();
  $("dirty").textContent = dirty ? "● " + t("unsaved") : "✓ " + t("saved");
  $("undo").disabled = !history.length;
  $("redo").disabled = !future.length;
}
function remember() {
  history.push(clone(state));
  if (history.length > 60) history.shift();
  future = [];
}
function commit(change, redraw = true, preview = true) {
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
      status(t("configured"));
      if (!running && preview) await frame();
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
  const label = el("label", paramLabel(key)),
    out = el("span", String(node.params[key]));
  label.append(out);
  const input = el("input");
  input.type = "range";
  [input.min, input.max, input.step] = limits[key];
  input.value = node.params[key];
  input.setAttribute("aria-label", `${blockLabel(node.kind)} ${key}`);
  input.oninput = () => (out.textContent = input.value);
  input.onchange = () => commit(() => (node.params[key] = Number(input.value)));
  input.onclick = (e) => e.stopPropagation();
  box.append(label, input);
  container.append(box);
}
function libraryLabel(entry) {
  return entry.type === "block" ? blockLabel(entry.kind) : entry.label;
}
function renderLibrary() {
  if (!catalog) return;
  const list = $("library"), category = $("libraryCategory").value || "all";
  list.replaceChildren();
  const groups = [...new Set(catalog.entries.map(e => e.group))];
  selectOptions($("libraryCategory"), [{id:"all",name:t("allGroups")}, ...groups.map(id=>({id,name:t(id)}))], category);
  const query = $("search").value.toLowerCase();
  const entries = catalog.entries.filter(e => (category === "all" || e.group === category) && `${libraryLabel(e)} ${e.id} ${e.expression || ""}`.toLowerCase().includes(query));
  const dropdown = $("librarySelect");
  dropdown.replaceChildren(new Option(t("chooseEntry") + ` (${entries.length})`, ""));
  for (const group of groups) {
    const options = entries.filter(e => e.group === group);
    if (!options.length) continue;
    const optgroup = el("optgroup"); optgroup.label = t(group);
    options.forEach(e => optgroup.append(new Option(libraryLabel(e), e.id)));
    dropdown.append(optgroup);
  }
  let previous;
  for (const entry of entries.slice(0, 45)) {
    if (previous !== entry.group) { list.append(el("h3",t(entry.group))); previous=entry.group; }
    const button = el("button", undefined, "library-card");
    button.dataset.entry = entry.id;
    if (entry.kind) button.dataset.kind = entry.kind;
    button.append(el("b", (entry.type === "block" || entry.type === "function" ? "＋ " : "↗ ") + libraryLabel(entry)),el("small",entry.expression || (entry.note ? t(entry.note) : entry.kind === "custom" ? "Python · JavaScript" : `OpenCV / ${entry.kind}`)));
    button.onclick = () => activateEntry(entry);
    button.draggable = ["block","function"].includes(entry.type);
    button.ondragstart = e => e.dataTransfer.setData("text/plain",JSON.stringify({entry:entry.id}));
    list.append(button);
  }
  if (!entries.length) list.append(el("p",t("noMatches")));
  if (entries.length > 45) list.append(el("p",t("moreCatalog")));
}
function activateEntry(entry, index) {
  if (entry.type === "block") return add(entry.kind, index);
  if (entry.type === "function") return add("algebra", index, {expression:entry.expression});
  const body=$("catalogBody"); body.replaceChildren(el("h2",entry.label),el("p",t(entry.note)));
  if (entry.signature) { const pre=el("pre",entry.signature);pre.dir="ltr";body.append(pre); }
  if (entry.source) {const a=el("a",t("sourceLink"));a.href=entry.source;a.target="_blank";a.rel="noopener";body.append(a);}
  if (entry.type === "example") {
    body.append(el("p",entry.state.nodes.map(n=>blockLabel(n.kind)).join(" → ")));
    const button=el("button",t("loadExample"),"primary");
    button.onclick=()=>{
      if (dirty && !confirm(t("confirmOpen"))) return;
      const next=clone(entry.state); next.view.locale=state.view.locale; next.view.codeLanguage=state.view.codeLanguage;
      $("catalogDetail").close();serial(()=>load(next));
    };body.append(button);
  }
  $("catalogDetail").showModal();
}
$("libraryCategory").onchange=renderLibrary;
$("librarySelect").onchange=()=>{ const entry=catalog.entries.find(e=>e.id===$("librarySelect").value);if(entry) activateEntry(entry);$("librarySelect").value=""; };
$("closeCatalog").onclick=()=>$("catalogDetail").close();
const codeDrafts = new Map();
function pendingCode() {
  return state?.nodes.some(n => n.kind === "custom" && codeDrafts.has(n.id+":"+(n.runtime || "python")) && codeDrafts.get(n.id+":"+(n.runtime || "python")) !== n.params.code);
}
function requireAppliedCode() { if (pendingCode()) throw Error(t("applyCode")); }

function add(kind, index = state.nodes.length, overrides = {}) {
  if (kind === "difference" && state.nodes.some((n) => n.kind === kind)) {
    status(t("exists"));
    return;
  }
  commit(() => {
    index = Math.max(2, index);
    const p = {...clone(blocks[kind].params), ...overrides},
      names = channels(index);
    if (p.input && !names.includes(p.input)) p.input = names.at(-1);
    if (p.expression && /\bdR\b/.test(p.expression) && !names.includes("dR"))
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
    if (node.kind === "source") card.dataset.sourceType = state.source.type;
    card.draggable = index >= 2;
    card.tabIndex = 0;
    card.onclick = () => {
      selected = node.id;
      renderGraph();
      renderInspector();
    };
    card.onkeydown = (e) => {
      if (e.target === card && e.key === "Enter") {
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
      el("h3", blockLabel(node.kind)),
    );
    card.append(head);
    if (node.params.expression)
      card.append(el("div", node.params.expression, "expression"));
    if (node.kind === "source")
      card.append(
        el(
          "div",
          `${t(state.source.type)} · ${state.source.type === "camera" ? t("camera") + " " + state.source.camera : t("sourceLocal")}`,
          "description",
        ),
      );
    else if (node.kind === "channels")
      card.append(el("div", t("normalized"), "description"));
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
      const close = el("button", "×", "node-close");
      close.type = "button";
      close.title = t("closeBlock");
      close.setAttribute(
        "aria-label",
        t("closeBlock") + ": " + blockLabel(node.kind),
      );
      close.onclick = (e) => {
        e.stopPropagation();
        removeNode(node.id);
      };
      close.onpointerdown = (e) => e.stopPropagation();
      card.append(close);
      const controls = el("div", undefined, "node-controls");
      for (const [text, title, fn] of [
        ["↑", t("earlier"), () => reorder(node.id, index - 1)],
        ["↓", t("later"), () => reorder(node.id, index + 1)],
      ]) {
        const b = el("button", text);
        b.title = title;
        b.dataset.action = text === "↑" ? "earlier" : "later";
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
function removeNode(id) {
  commit(() => {
    const index = state.nodes.findIndex((n) => n.id === id);
    if (index < 2) return;
    state.nodes.splice(index, 1);
    if (selected === id) selected = state.nodes[Math.max(0, index - 1)].id;
    for (const key of ["signal", "result"])
      if (!channels().includes(state.view[key])) state.view[key] = "R";
  });
}
function drop(e, index) {
  try {
    const data = JSON.parse(e.dataTransfer.getData("text/plain"));
    if (data.entry) { const entry=catalog.entries.find(e=>e.id===data.entry);if(entry)activateEntry(entry,index); }
    else if (data.kind && blocks[data.kind]) add(data.kind, index);
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
  $("selectedTitle").textContent = blockLabel(node.kind);
  $("parameters").replaceChildren();
  if (node.kind === "source") {
    const source = el("select");
    selectOptions(
      source,
      [
        { id: "synthetic", name: t("synthetic") },
        { id: "camera", name: t("camera") },
        { id: "image", name: t("image") },
        { id: "video", name: t("video") },
      ],
      state.source.type,
    );
    source.onchange = () => {
      if (["image", "video"].includes(source.value)) {
        $("media").click();
        source.value = state.source.type;
      } else commit(() => (state.source.type = source.value));
    };
    field(t("sourceChoice"), source);
    if (state.source.type === "camera") {
      const cam = el("input");
      cam.type = "number";
      cam.min = 0;
      cam.max = 16;
      cam.value = state.source.camera;
      cam.onchange = () =>
        commit(() => (state.source.camera = Number(cam.value)));
      field(t("cameraIndex"), cam);
    }
    const upload = el("button", t("chooseMedia"));
    upload.onclick = () => $("media").click();
    $("parameters").append(upload);
  } else if (["channels", "difference"].includes(node.kind)) {
    $("parameters").append(
      el(
        "p",
        node.kind === "difference" ? t("firstDifference") : t("confidenceHint"),
      ),
    );
  }
  if (!["source","channels","difference"].includes(node.kind)) {
    const language=el("select");language.id="blockRuntime";
    const current=node.runtime || "python";
    for (const [id, adapter] of Object.entries(catalog.runtimes)) {
      const compatible=adapter.available && (adapter.kinds==="*" || adapter.kinds.includes(node.kind));
      const option=new Option(adapter.name + (compatible ? "" : " · " + t(adapter.reason || "incompatible")),id);
      option.disabled=!compatible;language.append(option);
    }
    language.value=current;
    language.onchange=()=>{ running=false; return commit(()=>{
      if (node.kind==="custom") {
        codeDrafts.set(node.id+":"+current,$("customCode")?.value ?? node.params.code);
        node.params.code=codeDrafts.get(node.id+":"+language.value) || "";
      }
      node.runtime=language.value;
    },true,false); };
    field(t("runtime"),language);
    $("parameters").append(el("small",t("runtimeHint")));
  }
  for (const [key, value] of Object.entries(node.params)) {
    if (key === "code") continue;
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
        status(t("error") + ": " + e.message, true);
      }
    };
    field(key === "gain" && node.kind === "custom" ? t("customGain") : paramLabel(key), input);
  }
  if (node.kind === "custom") {
    const editor=el("textarea");editor.id="customCode";editor.rows=12;editor.spellcheck=false;editor.dir="ltr";
    const draftKey=node.id+":"+(node.runtime || "python");
    editor.value=codeDrafts.get(draftKey) ?? node.params.code;
    editor.placeholder=catalog.starters[node.runtime || "python"];
    editor.oninput=()=>{codeDrafts.set(draftKey,editor.value);mark();};
    field(t("code"),editor);
    $("parameters").append(el("p",t("codeContract")),el("small",t("codeHint")));
    const apply=el("button",t("applyCode"),"primary");apply.id="applyCode";
    apply.onclick=async()=>{
      running=false;
      try {await commit(()=>{node.params.code=editor.value;state.view.result=node.params.output;},true,false);await serial(()=>frame(true));} catch {}
    };
    $("parameters").append(apply);
  }
  if (state.nodes.indexOf(node)>=2) {
    const name=el("input");name.id="blockName";name.value=blockLabel(node.kind);name.maxLength=100;field(t("blockName"),name);
    const save=el("button",t("saveBlock"));save.id="saveBlock";
    save.onclick=()=>serial(async()=>{
      if (!valid) throw Error(t("fix"));
      requireAppliedCode();
      catalog=await api("/api/library/save",{state,selected:node.id,name:name.value});renderLibrary();status(t("blockSaved"));
    });$("parameters").append(save);
  }
  if ("input" in node.params) {
    const enabled = el("input");
    enabled.type = "checkbox";
    enabled.checked = node.enabled;
    enabled.onchange = () => commit(() => (node.enabled = enabled.checked));
    field(t("enabled"), enabled);
  }
  renderLesson(node);
}
function renderLesson(node) {
  const lesson = window.LESSONS?.find((l) => l.id === blocks[node.kind].lesson);
  const area = $("lesson");
  area.replaceChildren();
  if (blocks[node.kind].formula) {
    area.append(el("h3",blockLabel(node.kind)),el("div",blocks[node.kind].formula,"formula block-formula"),el("h3",t("backgroundLesson")));
  }
  if (!lesson) {
    area.append(el("p", t("missingLesson")));
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
  if (!["sl", "en"].includes(locale)) area.append(el("p", t("draft"), "draft"));
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
    el("summary", t("original")),
    el("p", lesson.summary.en),
    el("p", lesson.variables.en),
    el("p", lesson.caution.en),
  );
  area.append(detail);
  const link = el("button", t("fullLesson"), "text-button full-lesson");
  link.onclick = () => openClassroom(lesson.id);
  area.append(link);
  $("example").textContent = lesson[state.view.codeLanguage] || t("noExample");
}
function render() {
  try {
    localStorage.setItem("simplemotocam-studio-locale", state.view.locale);
  } catch {}
  translateInterface();
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
async function frame(runCode = false) {
  if (!valid) return;
  const data = await api("/api/frame", {runCode:runCode === true});
  if (data.needsCodeRun) {running=false;$("run").textContent="▶ "+t("run");status(t("needsCodeRun"));return;}
  if (data.ended) {
    running = false;
    $("run").textContent = "▶ " + t("run");
    status(t("ended"));
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
  $("status").dataset.frame = String(data.frame);
  status(
    `${t("frame")} ${data.frame} · ${data.processingMs} ms · ${data.ready ? t("historyReady") : t("firstFrame") + ": Δ = 0"}${data.size[0] !== data.originalSize[0] ? " · " + t("resized") : ""}`,
  );
}
async function loop() {
  if (!running) return;
  try {
    await serial(()=>frame(true));
  } catch {}
  if (running) setTimeout(loop, 70);
}
$("run").onclick = () => {
  if (!valid) {
    status(t("fix"), true);
    return;
  }
  running = !running;
  $("run").textContent = running ? "Ⅱ " + t("pause") : "▶ " + t("run");
  if (running) loop();
  else if (state.source.type === "camera") serial(() => api("/api/stop", {}));
};
$("step").onclick = () => serial(()=>frame(true));
$("name").onchange = () => commit(() => (state.name = $("name").value), false);
$("search").oninput = renderLibrary;
for (const key of ["signal", "result", "codeLanguage"])
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
    codeDrafts.clear();
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
    if (!valid) throw Error(t("fix"));
    requireAppliedCode();
    const record = await api("/api/save", state);
    saved = JSON.stringify(state);
    mark();
    download(JSON.stringify(record.state, null, 2), "simplemotocam-state.json");
    status(t("stateSaved"));
  });
$("export").onclick = () =>
  serial(async () => {
    if (!valid) throw Error(t("fix"));
    requireAppliedCode();
    download(
      await api("/api/export", state, true),
      "simplemotocam_algorithm.py",
      "text/x-python",
    );
    status(t("exported"));
  });
async function load(newState) {
  running = false;
  $("run").textContent = "▶ " + t("run");
  const r = await api("/api/config", newState);
  remember();
  state = r.state;
  codeDrafts.clear();
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
        if (dirty && !confirm(t("confirmOpen"))) return;
        serial(async () =>
          load(
            (await api("/api/projects/" + encodeURIComponent(item.id))).state,
          ),
        );
      };
      $("projectList").append(b);
    }
    if (!projects.length) $("projectList").append(el("p", t("noProjects")));
    $("projects").showModal();
  });
$("closeProjects").onclick = () => $("projects").close();
$("import").onchange = async () => {
  const file = $("import").files[0];
  if (!file) return;
  if (dirty && !confirm(t("confirmImport"))) return;
  serial(async () => {
    if (file.size > 262144) throw Error(t("jsonLarge"));
    const data = JSON.parse(await file.text());
    await load(data.state || data);
  });
  $("import").value = "";
};
$("media").onchange = () => {
  const file = $("media").files[0];
  if (!file) return;
  serial(async () => {
    if (file.size > 100 * 1024 * 1024) throw Error(t("mediaLarge"));
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
function syncClassroom(topic) {
  const frame = $("classroomFrame");
  if (!frame.getAttribute("src")) return;
  frame.contentWindow.postMessage(
    {
      type: "studio-learning-context",
      locale: state.view.locale,
      program: state.view.codeLanguage,
      topic,
    },
    location.origin,
  );
}
let classroomTopic;
function openClassroom(topic) {
  classroomTopic = topic;
  if (!$("classroom").open) $("classroom").showModal();
  let needsLesson = !$("classroomFrame").getAttribute("src");
  try {
    needsLesson ||=
      $("classroomFrame").contentWindow.location.pathname !==
      "/manuals/learning/index.html";
  } catch {
    needsLesson = true;
  }
  if (needsLesson)
    $("classroomFrame").src = "/manuals/learning/index.html?embedded=1";
  else syncClassroom(topic);
}
$("classroomFrame").onload = () => syncClassroom(classroomTopic);
$("closeClassroom").onclick = () => $("classroom").close();
$("guide").onclick = () => openClassroom();
$("libraryGuide").onclick = () => openClassroom();
function changeLocale(locale, program = state.view.codeLanguage) {
  if (!window.TRANSLATIONS.languages.some((l) => l.id === locale)) return;
  try {
    localStorage.setItem("simplemotocam-studio-locale", locale);
  } catch {}
  if (locale === state.view.locale && program === state.view.codeLanguage)
    return;
  commit(
    () => {
      state.view.locale = locale;
      state.view.codeLanguage = program;
    },
    true,
    false,
  );
}
$("locale").onchange = () => changeLocale($("locale").value);
window.addEventListener("message", (event) => {
  if (
    event.origin !== location.origin ||
    event.source !== $("classroomFrame").contentWindow
  )
    return;
  if (event.data?.type === "learning-close") $("classroom").close();
  if (
    event.data?.type === "learning-preference" &&
    ["python", "cpp", "c", "java"].includes(event.data.program)
  )
    changeLocale(event.data.locale, event.data.program);
});
window.addEventListener("beforeunload", (e) => {
  if (dirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});
async function start() {
  const data = await api("/api/bootstrap");
  ({ state, blocks, token, revision, catalog } = data);
  selectOptions(
    $("locale"),
    window.TRANSLATIONS?.languages || [
      { id: "sl", name: "Slovenščina" },
      { id: "en", name: "English" },
    ],
    state.view.locale,
  );
  try {
    const preferred = localStorage.getItem("simplemotocam-studio-locale");
    if (window.TRANSLATIONS.languages.some((l) => l.id === preferred))
      state.view.locale = preferred;
  } catch {}
  const configured = await api("/api/config", state);
  revision = configured.revision;
  render();
  await frame();
  await frame();
}
start().catch((e) => status(e.message, true));
