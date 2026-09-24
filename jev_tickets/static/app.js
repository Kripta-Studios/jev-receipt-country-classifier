"use strict";
const $ = (id) => document.getElementById(id);
const countries = {
  FR: "France",
  ES: "Spain",
  DE: "Germany",
  IT: "Italy",
  GB: "United Kingdom",
  US: "United States",
  CA: "Canada",
  OTHER: "Other country",
  UNKNOWN: "Unknown",
};
let config,
  saved,
  result,
  mode = "demo",
  file = null,
  previewURL = null,
  busy = false;
let ocrLines = [],
  hasImage = false,
  previewGeneration = 0;
let currentExample = null,
  lastExtraction = null,
  batchRunning = false,
  imageZoom = 1;

function status(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}
function setBusy(value) {
  busy = value;
  value = value || batchRunning;
  for (const id of [
    "demo-mode",
    "live-mode",
    "real-mode",
    "example",
    "real-example",
    "upload",
  ])
    $(id).disabled = value;
  $("compare").disabled =
    value ||
    (mode === "demo"
      ? !saved
      : !config?.jev_available || !$("receipt-text").value.trim());
  $("extract").disabled = value || !file || !config?.ocr_available;
  $("run-real").disabled =
    value || !config?.ocr_available || !config?.jev_available;
  $("run-all").disabled = $("run-real").disabled;
  $("receipt-text").readOnly = value || mode !== "live";
  $("workspace").setAttribute("aria-busy", String(value));
}
async function api(path, body) {
  const response = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || "The request could not be completed.");
  return data;
}
function clearResults() {
  result = null;
  $("results").replaceChildren();
  $("results").hidden = true;
  $("empty-results").hidden = false;
  $("result-notes").hidden = true;
  $("result-kind").textContent = "READY TO COMPARE";
  $("run-metrics").hidden = true;
}
function textCount() {
  $("text-count").textContent =
    `${$("receipt-text").value.length.toLocaleString()} CHARACTERS`;
  // Fit the actual wrapped content instead of clipping it in a fixed-height panel.
  $("receipt-text").style.height = "auto";
  $("receipt-text").style.height =
    `${Math.max(200, $("receipt-text").scrollHeight + 4)}px`;
}
window.addEventListener("resize", textCount);
function preview(src, caption) {
  const generation = ++previewGeneration;
  hasImage = Boolean(src);
  imageZoom = 1;
  $("receipt-canvas").style.width = "100%";
  $("receipt-canvas").style.height = "100%";
  $("open-image").hidden = !src;
  if (src) $("open-image").href = src;
  $("receipt-canvas").toggleAttribute("hidden", !src);
  $("text-preview").hidden = Boolean(src);
  $("text-preview").querySelector("strong").textContent = caption.startsWith(
    "PDF",
  )
    ? "PDF selected"
    : "Start with the text";
  $("text-preview").querySelector("p").textContent = caption.startsWith("PDF")
    ? "Extract its text below. Page-image overlays are available for image files."
    : mode === "demo"
      ? "This example uses a transcription. It skips the image-reading step."
      : "Choose an image to see it here, or paste text on the right.";
  $("ocr-boxes").replaceChildren();
  if (src) {
    const img = new Image();
    img.onload = () => {
      if (generation !== previewGeneration) return;
      $("receipt-canvas").setAttribute(
        "viewBox",
        `0 0 ${img.naturalWidth} ${img.naturalHeight}`,
      );
      $("receipt-image").setAttribute("href", src);
      $("receipt-image").setAttribute("width", img.naturalWidth);
      $("receipt-image").setAttribute("height", img.naturalHeight);
      drawBoxes();
    };
    img.onerror = () => {
      if (generation === previewGeneration)
        status("Image preview could not load.", true);
    };
    img.src = src;
  }
  $("preview-caption").textContent = caption;
}
function setLines(lines = []) {
  ocrLines = lines;
  $("ocr-lines").replaceChildren();
  $("ocr-details").hidden = !lines.length;
  $("line-count").textContent = `(${lines.length})`;
  $("selected-line").textContent =
    "Select a box or a text line to see the match.";
  lines.forEach((line, index) => {
    const button = node("button", "ocr-line");
    button.append(
      node("span", "line-number", String(index + 1).padStart(2, "0")),
      node("span", "line-text", line.text),
    );
    button.dataset.line = index;
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => selectLine(index));
    $("ocr-lines").append(button);
  });
  drawBoxes();
}
function drawBoxes() {
  const group = $("ocr-boxes");
  group.replaceChildren();
  const visible = hasImage && ocrLines.some((line) => Array.isArray(line.bbox));
  $("overlay-controls").hidden = !visible;
  group.classList.toggle("boxes-hidden", !$("show-boxes").checked);
  if (!hasImage) return;
  ocrLines.forEach((line, index) => {
    if (!Array.isArray(line.bbox) || line.page !== 1) return;
    const [x1, y1, x2, y2] = line.bbox;
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    for (const [name, value] of Object.entries({
      x: x1,
      y: y1,
      width: x2 - x1,
      height: y2 - y1,
      tabindex: 0,
      role: "button",
      "aria-label": `OCR line ${index + 1}: ${line.text}`,
      "aria-pressed": "false",
      "data-line": index,
    }))
      rect.setAttribute(name, value);
    rect.addEventListener("click", () => selectLine(index));
    rect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectLine(index);
      }
    });
    group.append(rect);
  });
}
function selectLine(index) {
  const line = ocrLines[index];
  document.querySelectorAll("[data-line]").forEach((el) => {
    const selected = Number(el.dataset.line) === index;
    el.classList.toggle("active", selected);
    el.setAttribute("aria-pressed", String(selected));
  });
  $("show-boxes").checked = true;
  $("ocr-boxes").classList.remove("boxes-hidden");
  $("ocr-details").open = true;
  const row = $("ocr-lines").querySelector(`[data-line="${index}"]`);
  if (row)
    $("ocr-lines").scrollTop = row.offsetTop - $("ocr-lines").offsetTop - 35;
  $("selected-line").textContent =
    `Line ${index + 1}: ${line.text}${line.confidence == null ? "" : ` · OCR score ${Math.round(line.confidence * 100)}%`}`;
  const start = $("receipt-text").value.indexOf(line.text);
  if (start >= 0)
    $("receipt-text").setSelectionRange(start, start + line.text.length);
}
$("show-boxes").addEventListener("change", () =>
  $("ocr-boxes").classList.toggle("boxes-hidden", !$("show-boxes").checked),
);
async function loadDemo() {
  lastExtraction = null;
  saved = null;
  clearResults();
  setBusy(true);
  status("Loading recorded example…");
  try {
    saved = await api("/api/demo", { id: $("example").value });
    $("receipt-text").value = saved.text;
    textCount();
    preview(
      saved.image,
      saved.image
        ? "SYNTHETIC RECEIPT / SAVED IMAGE"
        : "TEXT INPUT / NO OCR STEP",
    );
    setLines(saved.lines || []);
    $("source-note").textContent = `${saved.source} · ${saved.id}`;
    $("text-note").textContent = saved.image
      ? "Saved OCR output. Jev never receives the image."
      : "Saved text input. No OCR was needed.";
    status(saved.description);
  } catch (error) {
    status(error.message, true);
  } finally {
    setBusy(false);
  }
}
function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function render(data) {
  result = data;
  const target = $("results");
  target.replaceChildren();
  for (const answer of data.results) {
    const focused = answer.variant === "focused-v2";
    const card = node("article", `result-card${focused ? " focused" : ""}`);
    const top = node("div", "card-top");
    top.append(
      node("span", "", focused ? "FOCUSED PROMPT" : "ORIGINAL PROMPT"),
      node("span", "card-tag", "FOR REVIEW"),
    );
    card.append(top);
    if (answer.status === "error") {
      card.append(
        node("h3", "", "Request failed"),
        node("p", "help", answer.error),
      );
      target.append(card);
      continue;
    }
    const heading = node("div", "country-result");
    heading.append(
      node("h3", "", countries[answer.candidate] || answer.candidate),
      node("span", "country-code", answer.candidate),
    );
    card.append(heading);
    const score = node("div", "score-line");
    score.append(
      node("span", "", "MODEL PROBABILITY"),
      node("strong", "", `${Math.round(answer.probability * 100)}%`),
    );
    card.append(score);
    const bar = node("progress");
    bar.max = 1;
    bar.value = answer.probability;
    bar.setAttribute(
      "aria-label",
      `${focused ? "Focused" : "Original"} candidate probability`,
    );
    card.append(bar);
    const bottom = node("div", "card-bottom");
    bottom.append(
      node(
        "span",
        "",
        data.mode === "recorded"
          ? "Recorded response"
          : answer.cache_hit
            ? "Cached response"
            : `${answer.elapsed_s.toFixed(2)}s request`,
      ),
    );
    if (answer.location_evidence_probability != null)
      bottom.append(
        node(
          "span",
          "",
          `Evidence: ${Math.round(answer.location_evidence_probability * 100)}%`,
        ),
      );
    card.append(bottom);
    const facts = node("dl", "card-facts");
    const values = [
      ["API confidence", `${(answer.confidence * 100).toFixed(1)}%`],
      ["Top-two margin", `${(answer.margin * 100).toFixed(1)} pts`],
      [
        "Input / output tokens",
        `${answer.usage?.input_tokens ?? "—"} / ${answer.usage?.output_tokens ?? "—"}`,
      ],
      ["Request latency", `${(answer.elapsed_s || 0).toFixed(3)} s`],
      [
        data.mode === "recorded"
          ? "Historical cost estimate"
          : "Estimated request cost",
        money(
          answer.estimated_cost_usd ??
            ((answer.usage?.input_tokens || 0) * 0.042) / 1e6,
        ),
      ],
      ["Jev model", answer.model || "jev-1.13.0"],
    ];
    for (const [label, value] of values) {
      facts.append(node("dt", "", label), node("dd", "", value));
    }
    card.append(facts);
    const distribution = node("details", "distribution");
    distribution.append(node("summary", "", "All country probabilities"));
    for (const [label, p] of Object.entries(answer.probabilities).sort(
      (a, b) => b[1] - a[1],
    )) {
      const row = node("div", "distribution-row");
      row.append(
        node("span", "", countries[label] || label),
        node("strong", "", `${(p * 100).toFixed(1)}%`),
      );
      distribution.append(row);
    }
    card.append(distribution);
    target.append(card);
  }
  $("result-kind").textContent =
    data.mode === "recorded" ? "RECORDED COMPARISON" : "CURRENT COMPARISON";
  $("results").hidden = false;
  $("empty-results").hidden = true;
  $("result-notes").hidden = false;
  if (data.mode === "recorded") {
    const notes = {
      "eval-000001":
        "Both prompts select France. The input is saved local OCR from the synthetic image; showing it here does not run OCR again.",
      "eval-000004":
        "The original prompt abstains. The focused prompt selects the US, matching the generator's label. This is one example, not proof of general accuracy.",
      "control-shared-italian":
        "The expected answer is UNKNOWN: Italian language alone does not establish Italy. Here, the focused prompt makes an unsupported inference.",
    };
    $("comparison-note").textContent = notes[saved.id];
  } else
    $("comparison-note").textContent =
      "The focused prompt asks a separate evidence question. That percentage is a model judgment, not a validated reliability filter.";
  const rules = data.rules;
  $("rules-result").replaceChildren(
    node(
      "p",
      "",
      `Literal rules: ${countries[rules.country] || rules.country}. This narrow baseline does not override Jev.`,
    ),
  );
  for (const evidence of rules.evidence.slice(0, 6))
    $("rules-result").append(
      node("p", "", `${evidence.country} · ${evidence.quote}`),
    );
  if (!rules.evidence.length)
    $("rules-result").append(
      node("p", "", "No configured literal country signal matched."),
    );
  if (data.mode !== "recorded") renderMetrics(data);
}
function money(value) {
  return value == null ? "—" : `$${value.toFixed(6)}`;
}
function seconds(value) {
  return value == null ? "—" : `${value.toFixed(2)} s`;
}
function renderMetrics(data) {
  const metrics = data.metrics || {},
    extraction = data.extraction || lastExtraction;
  const target = $("run-metrics");
  target.replaceChildren();
  const values = [
    [
      "Total processing",
      seconds(
        metrics.total_s ?? metrics.jev_wall_s + (extraction?.elapsed_s || 0),
      ),
    ],
    ["Local OCR", seconds(extraction?.elapsed_s)],
    ["Jev comparison", seconds(metrics.jev_wall_s)],
    ["Estimated API cost", money(metrics.estimated_cost_usd)],
    [
      "Input / output tokens",
      `${metrics.input_tokens ?? 0} / ${metrics.output_tokens ?? 0}`,
    ],
    [
      "Mean OCR score",
      extraction?.mean_confidence == null
        ? "—"
        : `${(extraction.mean_confidence * 100).toFixed(1)}%`,
    ],
  ];
  for (const [label, value] of values) {
    const block = node("div", "run-metric");
    block.append(node("span", "", label), node("strong", "", value));
    target.append(block);
  }
  const note = node(
    "p",
    "metrics-note",
    `Fresh inference · ${!extraction ? "Text input; no OCR executed" : extraction.model_load_included ? "OCR model loading included" : "OCR session reused; image recomputed"} · ${metrics.successful_requests ?? 0}/2 Jev responses. Input $0.042/M tokens; output free. Cost is an estimate, excludes local compute${metrics.cost_is_partial ? ", and covers successful responses only" : ""}.`,
  );
  target.append(note);
  target.hidden = false;
}
function loadReal() {
  currentExample = config.real_examples.find(
    (row) => row.id === $("real-example").value,
  );
  if (!currentExample) return;
  clearResults();
  lastExtraction = null;
  setLines();
  $("receipt-text").value = "";
  textCount();
  $("challenge-note").textContent = currentExample.challenge;
  preview(currentExample.image, "REAL PHOTO / FRESH INFERENCE ON RUN");
  $("source-note").replaceChildren(
    node(
      "span",
      "",
      `${currentExample.id} · ${currentExample.attribution} · ${currentExample.license} · `,
    ),
  );
  const link = node("a", "", "Source image ↗");
  link.href = currentExample.source_url;
  link.target = "_blank";
  link.rel = "noreferrer";
  $("source-note").append(link);
  $("text-note").textContent =
    "Run the image through local OCR and both Jev prompts. No saved answers are loaded.";
  status(currentExample.challenge);
  setBusy(false);
}
async function runReal() {
  clearResults();
  setBusy(true);
  status(
    `Reading ${currentExample.id} with local OCR, then requesting both Jev decisions…`,
  );
  try {
    const data = await api("/api/run-example", { id: currentExample.id });
    lastExtraction = data.extraction;
    $("receipt-text").value = data.text;
    textCount();
    setLines(data.extraction.lines);
    $("text-note").textContent =
      `Fresh local OCR · ${data.extraction.line_count} lines · ${seconds(data.extraction.elapsed_s)}. All extracted text is displayed below.`;
    render(data);
    $("comparison-note").textContent =
      `Source reference: ${countries[data.example.expected]}. ${data.example.reference_evidence} Reference labels are not sent to Jev. OCR scores and model confidence are not verified accuracy.`;
    appendHistory(data);
    const failed = data.results.some((r) => r.status === "error");
    status(
      failed
        ? `Completed ${currentExample.id} with a Jev request failure. Check the result cards; the cost estimate is partial.`
        : `Completed ${currentExample.id} in ${seconds(data.metrics.total_s)}. New OCR computation and new Jev requests; no result-cache replay.`,
      failed,
    );
    return !failed;
  } catch (error) {
    status(error.message, true);
    appendHistory({ example: currentExample, error: error.message });
    return false;
  } finally {
    setBusy(false);
  }
}
function appendHistory(data) {
  const row = node("tr");
  const values = data.error
    ? [
        data.example.id,
        countries[data.example.expected],
        data.error,
        "—",
        "—",
        "—",
        "—",
        "—",
      ]
    : [
        data.example.id,
        countries[data.example.expected],
        ...data.results.map((r) =>
          r.status === "error"
            ? "Request failed"
            : `${countries[r.candidate]} ${r.candidate === data.example.expected ? "✓" : "≠"}`,
        ),
        seconds(data.extraction.elapsed_s),
        seconds(data.metrics.jev_wall_s),
        seconds(data.metrics.total_s),
        money(data.metrics.estimated_cost_usd),
      ];
  const labels = [
    "Receipt",
    "Store metadata",
    "Original",
    "Focused",
    "OCR",
    "Jev",
    "Total",
    "Est. API cost",
  ];
  values.forEach((value, index) => {
    const cell = node("td", "", value);
    cell.dataset.label = labels[index];
    row.append(cell);
  });
  $("history-rows").append(row);
  $("run-history").hidden = false;
}
$("real-mode").addEventListener("click", () => {
  if (busy) return;
  mode = "real";
  updateMode();
  loadReal();
});
$("real-example").addEventListener("change", loadReal);
$("run-real").addEventListener("click", runReal);
$("run-all").addEventListener("click", async () => {
  batchRunning = true;
  let failures = 0;
  try {
    for (const example of config.real_examples) {
      $("real-example").value = example.id;
      loadReal();
      if (!(await runReal())) failures++;
    }
  } finally {
    batchRunning = false;
    setBusy(false);
  }
  status(
    `All ${config.real_examples.length} examples processed; ${failures} runs with errors. Every run is listed in the session table.`,
    failures > 0,
  );
});
function zoom(value) {
  imageZoom = Math.max(1, Math.min(4, value));
  $("receipt-canvas").style.width = `${imageZoom * 100}%`;
  $("receipt-canvas").style.height = `${imageZoom * 100}%`;
}
$("zoom-in").addEventListener("click", () => zoom(imageZoom + 0.5));
$("zoom-out").addEventListener("click", () => zoom(imageZoom - 0.5));
$("zoom-fit").addEventListener("click", () => zoom(1));
$("demo-mode").addEventListener("click", async () => {
  if (busy) return;
  mode = "demo";
  updateMode();
  await loadDemo();
});
$("live-mode").addEventListener("click", () => {
  if (busy) return;
  mode = "live";
  lastExtraction = null;
  updateMode();
  clearResults();
  $("receipt-text").value = "";
  textCount();
  file = null;
  $("upload").value = "";
  preview(null, "YOUR RECEIPT / IMAGE OR TEXT");
  $("source-note").textContent =
    "Upload a receipt, or paste its text on the right.";
  setLines();
  $("text-note").textContent = "Review the text before sending it to Jev.";
  setBusy(false);
  status(
    config.jev_available
      ? "Paste text to compare, or upload a file and extract its text first."
      : "Live mode is not configured. Use the saved demo, or start the server locally with --live and an API key.",
    !config.jev_available,
  );
});
function updateMode() {
  for (const kind of ["real", "demo", "live"]) {
    $(`${kind}-mode`).classList.toggle("selected", mode === kind);
    $(`${kind}-mode`).setAttribute("aria-pressed", String(mode === kind));
  }
  $("demo-controls").hidden = mode !== "demo";
  $("upload-controls").hidden = mode !== "live";
  $("real-controls").hidden = mode !== "real";
  $("compare").hidden = mode === "real";
  $("mode-note").textContent =
    mode === "demo"
      ? "Recorded results. No API calls."
      : "Fresh local OCR + fresh Jev decisions. No response-cache replay.";
  $("ocr-note").textContent = config.ocr_available
    ? "Extraction stays local. Only the text is sent to Jev when you compare."
    : "OCR is unavailable. Start with the trace-it environment and model weights.";
}
$("example").addEventListener("change", loadDemo);
$("receipt-text").addEventListener("input", () => {
  // An edited transcription no longer corresponds exactly to the measured OCR run.
  lastExtraction = null;
  clearResults();
  textCount();
  setBusy(false);
});
$("compare").addEventListener("click", async () => {
  clearResults();
  setBusy(true);
  status(
    mode === "demo"
      ? "Showing saved responses…"
      : "Comparing both prompts with Jev…",
  );
  try {
    const data =
      mode === "demo"
        ? saved
        : await api("/api/compare", { text: $("receipt-text").value });
    render(data);
    status(
      data.results.some((r) => r.status === "error")
        ? "Comparison finished with a request error. Check the result cards."
        : mode === "demo"
          ? "Recorded comparison loaded. No OCR or API requests were made."
          : "Comparison complete. Candidates are suggestions for review.",
      data.results.some((r) => r.status === "error"),
    );
  } catch (error) {
    status(error.message, true);
  } finally {
    setBusy(false);
  }
});
$("upload").addEventListener("change", () => {
  lastExtraction = null;
  file = $("upload").files[0] || null;
  clearResults();
  setLines();
  $("receipt-text").value = "";
  textCount();
  if (previewURL) {
    URL.revokeObjectURL(previewURL);
    previewURL = null;
  }
  if (file && file.size > 10 * 1024 * 1024) {
    file = null;
    $("upload").value = "";
    preview(null, "FILE TOO LARGE");
    status("Choose a file no larger than 10 MiB.", true);
    setBusy(false);
    return;
  }
  if (file) {
    previewURL = file.type.startsWith("image/")
      ? URL.createObjectURL(file)
      : null;
    preview(
      previewURL,
      file.type === "application/pdf"
        ? "PDF INPUT / NO IMAGE PREVIEW"
        : "YOUR RECEIPT / LOCAL PREVIEW",
    );
    $("source-note").textContent = file.name;
    status("File selected. Extract its text before comparing.");
  }
  setBusy(false);
});
$("extract").addEventListener("click", async () => {
  if (!file) return;
  clearResults();
  setBusy(true);
  status(
    "Reading the file locally. The first OCR request can take a little longer…",
  );
  try {
    const encoded = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(",")[1]);
      reader.onerror = () => reject(new Error("The file could not be read."));
      reader.readAsDataURL(file);
    });
    const data = await api("/api/extract", { name: file.name, data: encoded });
    lastExtraction = data;
    $("receipt-text").value = data.text;
    textCount();
    setLines(data.lines);
    $("text-note").textContent =
      `Local extraction · ${data.line_count} lines · ${data.elapsed_s.toFixed(1)}s. You can edit the text.`;
    status(
      data.text.trim()
        ? "Text extracted. Review it, then compare prompts."
        : "No text was found. Try another image or paste a transcription.",
      !data.text.trim(),
    );
  } catch (error) {
    status(error.message, true);
  } finally {
    setBusy(false);
  }
});
$("download").addEventListener("click", () => {
  if (!result) return;
  const blob = new Blob(
    [JSON.stringify({ ...result, text: $("receipt-text").value }, null, 2)],
    { type: "application/json" },
  );
  const url = URL.createObjectURL(blob);
  const a = node("a");
  a.href = url;
  a.download = "receipt-comparison.json";
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
(async () => {
  try {
    config = await api("/api/config");
    const review = config.reviewed_evaluation?.variants;
    if (review) {
      const measurements = [
        ["Matches store metadata", "metadata_matches", "n"],
        ["Matches reviewed image evidence", "reviewed_image_matches", "n"],
        [
          "Correct country on observable images",
          "observable_correct",
          "image_country_observable",
        ],
        [
          "Reasonable UNKNOWN on indeterminate images",
          "reasonable_abstentions",
          "image_country_unobservable",
        ],
        [
          "Unsupported country assertions",
          "unsupported_country_assertions",
          "image_country_unobservable",
        ],
        ["Extraction / request failures", "errors", "n"],
      ];
      for (const [label, key, denominator] of measurements) {
        const row = node("tr");
        const values = [
          label,
          ...["baseline-v1", "focused-v2"].map(
            (v) => `${review[v][key]} / ${review[v][denominator]}`,
          ),
        ];
        values.forEach((value, i) => {
          const cell = node("td", "", value);
          cell.dataset.label = [
            "Measurement",
            "Original prompt",
            "Focused prompt",
          ][i];
          row.append(cell);
        });
        $("reviewed-rows").append(row);
      }
    }
    $("real-example").replaceChildren(
      ...config.real_examples.map((row) => {
        const option = node(
          "option",
          "",
          `${countries[row.expected]} · ${row.title}`,
        );
        option.value = row.id;
        return option;
      }),
    );
    $("example").replaceChildren(
      ...config.examples.map((row) => {
        const option = node("option", "", row.title);
        option.value = row.id;
        return option;
      }),
    );
    // Keep current decisions visible above the complete, expandable text rather than below it.
    $("results")
      .closest(".analysis-panel")
      .prepend(document.querySelector(".results-section"));
    mode = config.jev_available && config.ocr_available ? "real" : "demo";
    updateMode();
    if (mode === "real") loadReal();
    else await loadDemo();
  } catch (error) {
    status(`Playground could not start: ${error.message}`, true);
  }
})();
