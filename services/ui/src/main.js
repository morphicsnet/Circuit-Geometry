const apiBaseInput = document.getElementById("apiBase");
const workspaceInput = document.getElementById("workspace");
const laneInput = document.getElementById("lane");
const behaviorInput = document.getElementById("behavior");
const modelInput = document.getElementById("model");
const runBtn = document.getElementById("runBtn");
const refreshBtn = document.getElementById("refreshBtn");
const exportBtn = document.getElementById("exportBtn");
const runList = document.getElementById("runList");
const runSummary = document.getElementById("runSummary");
const determinismSummary = document.getElementById("determinismSummary");
const artifactSummary = document.getElementById("artifactSummary");

const state = {
  selectedRunId: null,
  runs: [],
};

function apiBase() {
  return apiBaseInput.value.trim().replace(/\/+$/, "");
}

function workspace() {
  return workspaceInput.value.trim();
}

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

function badgeClass(conformanceClass) {
  if (conformanceClass === "conformant") return "badge conformant";
  if (conformanceClass === "provisional") return "badge provisional";
  return "badge rejected";
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, options);
  if (!response.ok) {
    let details = response.statusText;
    try {
      const body = await response.json();
      details = body.detail || details;
    } catch (_) {
      // ignore parse error for non-json body
    }
    throw new Error(`${response.status}: ${details}`);
  }
  return response.json();
}

function renderRuns() {
  runList.innerHTML = "";
  if (state.runs.length === 0) {
    runList.innerHTML = "<li class='run-item'>No runs yet.</li>";
    return;
  }
  for (const run of state.runs) {
    const item = document.createElement("li");
    item.className = "run-item";
    item.dataset.selected = String(run.run_id === state.selectedRunId);
    item.innerHTML = `
      <div><strong>${run.run_id}</strong></div>
      <div class="run-meta">
        <span>${run.model_id}</span>
        <span class="${badgeClass(run.conformance_class)}">${run.conformance_class}</span>
      </div>
      <div class="run-meta">
        <span>${run.lane_id}</span>
        <span>${new Date(run.created_at).toLocaleString()}</span>
      </div>
    `;
    item.addEventListener("click", () => {
      state.selectedRunId = run.run_id;
      renderRuns();
      loadRunDetails(run.run_id);
    });
    runList.appendChild(item);
  }
}

async function loadRuns(selectLatest = false) {
  try {
    const payload = await requestJson(
      `/runs?workspace=${encodeURIComponent(workspace())}`
    );
    state.runs = payload.runs || [];
    if (selectLatest && state.runs.length > 0) {
      state.selectedRunId = state.runs[0].run_id;
    }
    if (!state.selectedRunId && state.runs.length > 0) {
      state.selectedRunId = state.runs[0].run_id;
    }
    renderRuns();
    if (state.selectedRunId) {
      await loadRunDetails(state.selectedRunId);
    }
  } catch (error) {
    runSummary.textContent = `Failed to load runs:\n${String(error)}`;
  }
}

async function loadRunDetails(runId) {
  try {
    const [runPayload, determinismPayload] = await Promise.all([
      requestJson(
        `/runs/${encodeURIComponent(runId)}?workspace=${encodeURIComponent(workspace())}`
      ),
      requestJson(
        `/runs/${encodeURIComponent(runId)}/determinism?workspace=${encodeURIComponent(workspace())}`
      ),
    ]);

    runSummary.textContent = formatJson(runPayload.run);
    determinismSummary.textContent = formatJson(determinismPayload);

    const artifactView = {
      atlas_overlap_map:
        runPayload.artifacts?.atlas_overlap_map?.payload?.overlap_score ?? null,
      candidate_event_count:
        runPayload.artifacts?.candidate_event_table?.payload?.candidate_count ?? null,
      admitted_hyperpath_count:
        runPayload.artifacts?.admitted_hyperpath_table?.payload?.admitted_count ?? null,
      falsifier_sheet: runPayload.artifacts?.falsifier_sheet?.payload ?? null,
    };
    artifactSummary.textContent = formatJson(artifactView);
  } catch (error) {
    runSummary.textContent = `Failed to load run details:\n${String(error)}`;
    determinismSummary.textContent = "No run selected.";
    artifactSummary.textContent = "No run selected.";
  }
}

async function runBenchmark() {
  runBtn.disabled = true;
  try {
    const payload = {
      workspace: workspace(),
      lane_id: laneInput.value.trim(),
      behavior_id: behaviorInput.value.trim(),
      model_id: modelInput.value.trim(),
      atlas_profile: behaviorInput.value.trim(),
    };
    const created = await requestJson("/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.selectedRunId = created.run_id;
    await loadRuns();
  } catch (error) {
    runSummary.textContent = `Benchmark run failed:\n${String(error)}`;
  } finally {
    runBtn.disabled = false;
  }
}

async function exportSelected() {
  if (!state.selectedRunId) {
    runSummary.textContent = "Select a run before exporting.";
    return;
  }
  exportBtn.disabled = true;
  try {
    const exported = await requestJson(
      `/runs/${encodeURIComponent(state.selectedRunId)}/export?workspace=${encodeURIComponent(
        workspace()
      )}`,
      { method: "POST" }
    );
    artifactSummary.textContent = `${artifactSummary.textContent}\n\nExport:\n${formatJson(
      exported
    )}`;
  } catch (error) {
    artifactSummary.textContent = `Export failed:\n${String(error)}`;
  } finally {
    exportBtn.disabled = false;
  }
}

runBtn.addEventListener("click", runBenchmark);
refreshBtn.addEventListener("click", () => loadRuns(true));
exportBtn.addEventListener("click", exportSelected);

loadRuns(true);
