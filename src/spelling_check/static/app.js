const form = document.querySelector("#run-form");
const statusEl = document.querySelector("#status");
const button = document.querySelector("#run-button");
const summaryEl = document.querySelector("#summary");
const metricsEl = document.querySelector("#metrics");
const casesEl = document.querySelector("#cases");

loadDefaults();

async function loadDefaults() {
  const response = await fetch("/api/defaults");
  const data = await response.json();
  const settings = data.settings || {};
  const config = settings.config || {};
  document.querySelector("#base-url").value = settings.base_url || "";
  document.querySelector("#model").value = settings.model || "";
  document.querySelector("#timeout").value = settings.timeout || 30;
  document.querySelector("#risk-threshold").value = config.risk_threshold || 7;
  document.querySelector("#score-batch-size").value = config.score_batch_size || 1;
}

function settings() {
  const apiKey = document.querySelector("#api-key").value.trim();
  const data = {
    base_url: document.querySelector("#base-url").value.trim(),
    model: document.querySelector("#model").value.trim(),
    timeout: Number(document.querySelector("#timeout").value || 30),
    config: {
      risk_threshold: Number(document.querySelector("#risk-threshold").value || 7),
      score_batch_size: Number(document.querySelector("#score-batch-size").value || 1)
    }
  };
  if (apiKey) data.api_key = apiKey;
  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  statusEl.textContent = "Running...";
  statusEl.className = "status";
  summaryEl.innerHTML = "";
  metricsEl.innerHTML = "";
  casesEl.innerHTML = "";
  try {
    const file = document.querySelector("#file").files[0];
    let response;
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("text", document.querySelector("#text").value);
      formData.append("settings", JSON.stringify(settings()));
      response = await fetch("/api/run", { method: "POST", body: formData });
    } else {
      response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: document.querySelector("#text").value, settings: settings() })
      });
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    render(data);
    statusEl.textContent = "Done";
  } catch (error) {
    statusEl.textContent = error.message;
    statusEl.className = "status error";
    casesEl.innerHTML = '<div class="empty">No results.</div>';
  } finally {
    button.disabled = false;
  }
});

function render(data) {
  const summary = data.summary || {};
  summaryEl.innerHTML = [
    metric("Cases", summary.case_count),
    metric("Corrected", summary.corrected),
    metric("Suspicious", summary.suspicious_count),
    metric("Candidates", summary.candidate_count)
  ].join("");
  metricsEl.innerHTML = data.metrics ? renderMetrics(data.metrics) : "";
  const cases = data.cases || [];
  casesEl.className = "";
  casesEl.innerHTML = cases.length ? cases.map(renderCase).join("") : '<div class="empty">No cases.</div>';
}

function metric(label, value) {
  return `<div class="metric">${escapeHtml(label)}<strong>${value ?? 0}</strong></div>`;
}

function renderMetrics(metrics) {
  return `<table style="margin-bottom:14px"><tbody>
    <tr><th>Detection P/R/F1</th><td>${fmt(metrics.detection_precision)} / ${fmt(metrics.detection_recall)} / ${fmt(metrics.detection_f1)}</td></tr>
    <tr><th>Correction P/R/F1</th><td>${fmt(metrics.correction_precision)} / ${fmt(metrics.correction_recall)} / ${fmt(metrics.correction_f1)}</td></tr>
    <tr><th>FPR</th><td>${fmt(metrics.false_positive_rate)} (${metrics.false_positive_positions} / ${metrics.gold_non_error_positions})</td></tr>
  </tbody></table>`;
}

function renderCase(item) {
  const corrections = item.corrections || [];
  const review = analyzeCase(item);
  return `<article class="case">
    <div class="case-head"><strong>${escapeHtml(item.id || "")}</strong><span class="badge ${escapeHtml(item.status || "")}">${escapeHtml(item.status || "parsed")}</span></div>
    ${renderReviewStats(review)}
    ${renderAlignment(item, review)}
    ${renderLegend(review)}
    ${corrections.length ? renderCorrections(corrections, item, review) : '<div class="empty">No candidate corrections.</div>'}
  </article>`;
}

function renderReviewStats(review) {
  if (!review.hasGold) {
    return `<div class="case-stats">
      <span class="stat-chip">Changed ${review.changed}</span>
      <span class="stat-chip warn">Suspicious ${review.suspicious}</span>
    </div>`;
  }
  return `<div class="case-stats">
    <span class="stat-chip good">Correct ${review.correct}</span>
    <span class="stat-chip bad">Wrong ${review.wrong}</span>
    <span class="stat-chip warn">Missed ${review.missed}</span>
    <span class="stat-chip warn">Over-edit ${review.overedit}</span>
  </div>`;
}

function renderAlignment(item, review) {
  const input = Array.from(item.input || "");
  const rows = [alignmentRow("Original", input, review, "input")];
  if (review.hasGold) rows.push(alignmentRow("Gold", Array.from(item.gold || ""), review, "gold"));
  return `<div class="review">${rows.join("")}</div>`;
}

function renderLegend(review) {
  if (review.hasGold) {
    return `<div class="legend">
      ${legendItem("char-pred-correct", "model fixed correctly")}
      ${legendItem("char-pred-wrong", "model changed wrongly")}
      ${legendItem("char-missed", "gold error missed")}
      ${legendItem("char-overedit", "normal char would be over-edited")}
      ${legendItem("char-suspicious", "suspicious only")}
    </div>`;
  }
  return `<div class="legend">
    ${legendItem("char-pred-correct", "model changed")}
    ${legendItem("char-suspicious", "suspicious only")}
  </div>`;
}

function legendItem(className, label) {
  return `<span class="legend-item"><span class="legend-swatch ${className}"></span>${escapeHtml(label)}</span>`;
}

function alignmentRow(label, chars, review, row) {
  const cells = chars.map((char, index) => {
    const classes = ["char-cell"];
    if (char.trim() === "") classes.push("char-space");
    classes.push(...cellClasses(index, row, review));
    return `<span class="${classes.join(" ")}">${escapeHtml(char) || "&nbsp;"}</span>`;
  }).join("");
  return `<div class="alignment-row"><div class="row-label">${label}</div><div class="aligned-text">${cells}</div></div>`;
}

function cellClasses(index, row, review) {
  const changed = review.changedIndexes.has(index);
  const goldError = review.goldErrorIndexes.has(index);
  const suspicious = review.suspiciousIndexes.has(index);
  if (row === "gold" && goldError) return ["char-missed"];
  if (row === "input" && changed && goldError && review.modelChars[index] === review.goldChars[index]) return ["char-pred-correct"];
  if (row === "input" && changed && goldError) return ["char-pred-wrong"];
  if (row === "input" && changed && !goldError && review.hasGold) return ["char-overedit"];
  if (row === "input" && !changed && goldError) return ["char-missed"];
  if (row === "input" && suspicious && !goldError) return ["char-suspicious"];
  if (row === "input" && suspicious) return ["char-suspicious"];
  if (!review.hasGold && row === "input" && changed) return ["char-pred-correct"];
  return [];
}

function analyzeCase(item) {
  const inputChars = Array.from(item.input || "");
  const modelChars = Array.from(item.corrected_text || item.input || "");
  const goldChars = item.gold ? Array.from(item.gold) : [];
  const suspiciousIndexes = new Set((item.suspicious_chars || []).map((risk) => risk.index));
  const changedIndexes = new Set();
  const goldErrorIndexes = new Set();
  const length = Math.max(inputChars.length, modelChars.length, goldChars.length);
  let correct = 0;
  let wrong = 0;
  let missed = 0;
  let overedit = 0;
  for (let index = 0; index < length; index += 1) {
    const inputChar = inputChars[index] ?? "";
    const modelChar = modelChars[index] ?? "";
    const goldChar = goldChars[index] ?? "";
    const changed = modelChar !== inputChar;
    const goldError = item.gold ? goldChar !== inputChar : false;
    if (changed) changedIndexes.add(index);
    if (goldError) goldErrorIndexes.add(index);
    if (!item.gold) continue;
    if (changed && goldError && modelChar === goldChar) correct += 1;
    else if (changed && goldError) wrong += 1;
    else if (!changed && goldError) missed += 1;
    else if (changed && !goldError) overedit += 1;
  }
  return {
    hasGold: Boolean(item.gold),
    inputChars,
    modelChars,
    goldChars,
    suspiciousIndexes,
    changedIndexes,
    goldErrorIndexes,
    changed: changedIndexes.size,
    suspicious: suspiciousIndexes.size,
    correct,
    wrong,
    missed,
    overedit
  };
}

function renderCorrections(corrections, item, review) {
  const rows = corrections.map((correction) => `<tr>
    <td>${correction.index}</td>
    <td>${escapeHtml(correction.original_char)} -> ${escapeHtml(correction.candidate_char)}</td>
    <td>${candidateJudgment(correction, item, review)}</td>
    <td>${fmt(correction.delta)}</td>
    <td>${fmt(correction.original_score)} / ${fmt(correction.candidate_score)}</td>
    <td>${escapeHtml(correction.source)}</td>
  </tr>`).join("");
  return `<table style="margin-top:12px"><thead><tr><th>Index</th><th>Candidate</th><th>Judgment</th><th>Delta</th><th>Score</th><th>Source</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function candidateJudgment(correction, item, review) {
  const index = correction.index;
  const applied = review.modelChars[index] === correction.candidate_char;
  if (!review.hasGold) {
    return `<span class="candidate-judgment${applied ? " good" : ""}">${applied ? "Applied" : "Candidate"}</span>`;
  }
  const goldChar = review.goldChars[index];
  const goldError = review.goldErrorIndexes.has(index);
  if (applied && goldError && correction.candidate_char === goldChar) return '<span class="candidate-judgment good">Correct</span>';
  if (applied && correction.candidate_char !== goldChar) return '<span class="candidate-judgment bad">Wrong</span>';
  if (!applied && goldError && correction.candidate_char === goldChar) return '<span class="candidate-judgment warn">Could fix</span>';
  if (!goldError) return '<span class="candidate-judgment warn">Over-edit</span>';
  return '<span class="candidate-judgment">Candidate</span>';
}

function fmt(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(4) : "";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
}
