/*
 * app.js
 * ======
 * Frontend logic for AutoBIDSify Desktop.
 *
 * Talks to Python through the pywebview bridge:
 *   - call Python:  await window.pywebview.api.<method>(...)
 *   - Python -> UI: Python calls window.appendLog(...) and window.setState(...)
 *
 * State held here: the chosen bundle paths, input dir, and output dir.
 */

(function () {
  "use strict";

  // ---- application state ----
  const state = {
    bundlePaths: [],
    bundleResult: null,
    inputDir: null,
    outputDir: null,
    running: false,
  };

  const REQUIRED = [
    "BIDSPlan.yaml", "mat_mapping.json",
    "dataset_description.json", "README.md", "participants.tsv",
  ];
  const OPTIONAL = ["headers_normalized.json", "voxel_final_plan.json"];

  // ---- element refs ----
  const $ = (id) => document.getElementById(id);
  const dropzone = $("dropzone");
  const statusLine = $("statusLine");
  const inputField = $("inputField");
  const outputField = $("outputField");
  const runBtn = $("runBtn");
  const openBtn = $("openBtn");
  const logEl = $("log");
  const stateEl = $("state");

  // ---- theme toggle ----
  $("themeToggle").addEventListener("click", () => {
    const root = document.documentElement;
    const isLight = root.getAttribute("data-theme") === "light";
    root.setAttribute("data-theme", isLight ? "dark" : "light");
  });

  // ---- bundle: browse + drag/drop ----
  $("browseBtn").addEventListener("click", async () => {
    const files = await window.pywebview.api.pick_files();
    if (files && files.length) handleBundlePaths(files);
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("hover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("hover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("hover");
    // pywebview exposes dropped file paths on the event's dataTransfer files;
    // each file has a .name but native paths come via the bridge differently
    // across platforms, so we fall back to the file picker when paths are
    // unavailable. Most reliable cross-platform path is the Browse button.
    const paths = [];
    if (e.dataTransfer && e.dataTransfer.files) {
      for (const f of e.dataTransfer.files) {
        if (f.path) paths.push(f.path); // available on some backends
      }
    }
    if (paths.length) handleBundlePaths(paths);
  });

  async function handleBundlePaths(paths) {
    state.bundlePaths = paths;
    state.bundleResult = await window.pywebview.api.resolve_bundle(paths);
    renderChips();
    refreshRunEnabled();
  }

  function renderChips() {
    const found = (state.bundleResult && state.bundleResult.found) || {};
    const all = REQUIRED.concat(OPTIONAL);
    statusLine.innerHTML = "";
    for (const name of all) {
      const span = document.createElement("span");
      if (found[name]) {
        span.className = "chip ok";
        span.innerHTML = `<span class="tick">✓</span>${name}`;
      } else if (REQUIRED.includes(name)) {
        span.className = "chip miss";
        span.innerHTML = `<span class="tick">✗</span>${name}`;
      } else {
        span.className = "chip opt";
        span.innerHTML = `<span class="tick">○</span>${name} (optional)`;
      }
      statusLine.appendChild(span);
    }
  }

  // ---- folder pickers ----
  $("inputBtn").addEventListener("click", async () => {
    const dir = await window.pywebview.api.pick_folder();
    if (dir) {
      state.inputDir = dir;
      inputField.textContent = dir;
      inputField.classList.remove("ph");
      refreshRunEnabled();
    }
  });
  $("outputBtn").addEventListener("click", async () => {
    const dir = await window.pywebview.api.pick_folder();
    if (dir) {
      state.outputDir = dir;
      outputField.textContent = dir;
      outputField.classList.remove("ph");
      refreshRunEnabled();
    }
  });

  // ---- run gating ----
  function refreshRunEnabled() {
    const ready =
      state.bundleResult && state.bundleResult.is_complete &&
      state.inputDir && state.outputDir && !state.running;
    runBtn.disabled = !ready;
  }

  // ---- execute ----
  runBtn.addEventListener("click", async () => {
    if (runBtn.disabled) return;
    logEl.innerHTML = "";
    openBtn.disabled = true;
    const res = await window.pywebview.api.run_pipeline({
      bundle_paths: state.bundlePaths,
      input_dir: state.inputDir,
      output_dir: state.outputDir,
      validate: $("validateChk").checked,
    });
    if (!res || !res.started) return;
  });

  $("clearBtn").addEventListener("click", () => { logEl.innerHTML = ""; });

  openBtn.addEventListener("click", () => {
    if (state.outputDir) window.pywebview.api.open_output(state.outputDir);
  });

  // ---- updates pushed from Python ----
  // colorize by tag and append a line, then scroll to bottom.
  window.appendLog = function (line) {
    const div = document.createElement("div");
    let cls = "";
    if (line.includes("[FATAL]") || line.includes("[ERROR]")) cls = "err";
    else if (line.includes("[WARN")) cls = "warn";
    else if (line.includes("✓") || /complete|done\.?$/i.test(line)) cls = "ok";
    else if (line.includes("[INFO]") || line.includes("[WORKER]")) cls = "tag";
    div.className = cls;
    div.textContent = line;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  };

  window.setState = function (s) {
    state.running = (s === "running");
    const labels = { idle: "IDLE", running: "● RUNNING", done: "● DONE", error: "● ERROR" };
    stateEl.className = "state " + (s === "idle" ? "" : s);
    stateEl.innerHTML = `<span class="dot"></span>${labels[s] || "IDLE"}`;
    if (s === "done") openBtn.disabled = false;
    refreshRunEnabled();
  };
})();