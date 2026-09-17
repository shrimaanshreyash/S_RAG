const byId = (id) => document.getElementById(id);
const state = {
  selectedFiles: [], status: null, handoffCaseId: null, reviewPacket: null, reviews: [],
  lastAgentExperiment: null, repairQuestion: null, repairAnswer: null, repairPatch: null,
};

function duration(seconds) {
  if (seconds === null || seconds === undefined) return "--";
  return seconds < 1 ? `${(seconds * 1000).toFixed(1)} ms` : `${seconds.toFixed(2)} s`;
}
function integer(value) { return value === null || value === undefined ? "--" : Number(value).toLocaleString(); }
async function api(path, options = {}) {
  const response = await fetch(path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}
function setMessage(message, kind = "info") {
  const target = byId("uploadMessage");
  target.hidden = !message; target.dataset.kind = kind; target.textContent = message;
}
function setHandoffMessage(message, kind = "info") {
  const target = byId("handoffMessage");
  target.hidden = !message; target.dataset.kind = kind; target.textContent = message;
}
function causeLabel(value) {
  return value.split("_").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}
function switchView(view) {
  const handoffActive = view === "handoff";
  byId("handoffView").hidden = !handoffActive; byId("ragView").hidden = handoffActive;
  byId("handoffTab").classList.toggle("is-active", handoffActive);
  byId("ragTab").classList.toggle("is-active", !handoffActive);
}
function updateAgentButton() {
  const button = byId("runHandoffAgent");
  const ready = Boolean(
    state.status?.ollama_ready
      && state.status?.generation_ready
      && state.status?.embedding_ready
      && state.handoffCaseId,
  );
  button.disabled = !ready;
  button.title = ready ? "" : "Ollama, both configured models, and a handover case are required.";
}
function renderHandoffCaseList(cases) {
  const container = byId("handoffCases"); container.replaceChildren();
  byId("handoffCaseCount").textContent = cases.length;
  if (!cases.length) {
    const empty = document.createElement("p"); empty.className = "document-meta";
    empty.textContent = "No cases yet. Create the GitLab benchmark or synthetic control."; container.append(empty); return;
  }
  cases.forEach((item) => {
    const button = document.createElement("button"); button.type = "button"; button.className = "document-item";
    if (item.case_id === state.handoffCaseId) button.classList.add("is-selected");
    button.addEventListener("click", () => loadHandoffCase(item.case_id));
    const name = document.createElement("span"); name.className = "document-name"; name.textContent = item.title;
    const meta = document.createElement("span"); meta.className = "document-meta";
    meta.textContent = `${item.task_count} tasks | ${item.phase.replaceAll("_", " ")}`;
    button.append(name, meta); container.append(button);
  });
}
async function loadHandoffCases() {
  try {
    const response = await api("/api/handoff/cases"); renderHandoffCaseList(response.cases);
    if (response.cases.length && !state.handoffCaseId) await loadHandoffCase(response.cases[0].case_id);
  } catch (error) { setHandoffMessage(error.message, "error"); }
}
function renderHandoffTasks(tasks) {
  const container = byId("handoffTasks"); container.replaceChildren();
  const taskSelect = byId("agentTaskSelect"); const previousTask = taskSelect.value;
  taskSelect.replaceChildren();
  tasks.forEach((task, index) => {
    const option = document.createElement("option"); option.value = task.task_id;
    option.textContent = `${index + 1}. ${task.title}`; taskSelect.append(option);
    const card = document.createElement("article"); card.className = "handoff-task";
    const heading = document.createElement("div"); heading.className = "task-heading";
    const number = document.createElement("span"); number.className = "task-number"; number.textContent = String(index + 1).padStart(2, "0");
    const copy = document.createElement("div"); const title = document.createElement("h3"); title.textContent = task.title;
    const objective = document.createElement("p"); objective.textContent = task.objective; copy.append(title, objective);
    const badge = document.createElement("span"); badge.className = `cause-badge cause-${task.expected_failure_cause}`; badge.textContent = causeLabel(task.expected_failure_cause);
    heading.append(number, copy, badge);
    const details = document.createElement("div"); details.className = "task-details";
    details.textContent = `Verifier: ${task.verifier_id} · ${task.success_criteria.join(" · ")}`;
    card.append(heading, details); container.append(card);
  });
  if ([...taskSelect.options].some((option) => option.value === previousTask)) taskSelect.value = previousTask;
}
async function loadHandoffCase(caseId) {
  try {
    const bundle = await api(`/api/handoff/cases/${encodeURIComponent(caseId)}`);
    state.handoffCaseId = caseId; byId("handoffEmpty").hidden = true; byId("handoffCaseDetail").hidden = false;
    byId("handoffTitle").textContent = bundle.case.title; byId("handoffRole").textContent = bundle.case.role;
    byId("handoffCorpus").textContent = bundle.case.current_corpus_version_id;
    byId("handoffTaskCount").textContent = bundle.tasks.length; byId("handoffPhase").textContent = bundle.case.phase.replaceAll("_", " ");
    byId("handoffBenchmarkStatus").textContent = causeLabel(bundle.case.benchmark_status);
    byId("handoffKicker").textContent = bundle.case.provenance ? "Phase 7 · hardened source benchmark" : "Phase 1–5 · synthetic control";
    const provenance = byId("benchmarkProvenance");
    provenance.hidden = !bundle.case.provenance;
    if (bundle.case.provenance) {
      const source = bundle.case.provenance;
      provenance.textContent = `Integrity verified · ${source.verified_file_count} pinned files · commit ${source.commit.slice(0, 12)} · ${source.license} · simulated tools · human review pending`;
    } else provenance.textContent = "";
    byId("benchmarkReportPanel").hidden = !bundle.case.provenance;
    byId("reviewPanel").hidden = !bundle.case.provenance;
    byId("reviewWorkspace").hidden = true;
    byId("reviewState").textContent = bundle.case.benchmark_status === "human_reviewed" ? "Review complete" : "Not started";
    byId("benchmarkReportOutcome").hidden = true;
    byId("benchmarkReportState").textContent = "Awaiting latest report";
    renderHandoffTasks(bundle.tasks); byId("rehearsalResults").hidden = true; byId("agentResults").hidden = true; byId("repairResults").hidden = true;
    updateAgentButton();
    const response = await api("/api/handoff/cases"); renderHandoffCaseList(response.cases);
  } catch (error) { setHandoffMessage(error.message, "error"); }
}
async function initializeHandoff() {
  const button = byId("initializeHandoff"); button.disabled = true; button.textContent = "Creating...";
  try {
    const bundle = await api("/api/handoff/synthetic", { method: "POST" });
    setHandoffMessage("Synthetic case persisted locally. No AI-agent run has been claimed.");
    await loadHandoffCase(bundle.case.case_id);
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Create synthetic control"; }
}
async function initializeGitlabBenchmark() {
  const button = byId("initializeGitlab"); button.disabled = true; button.textContent = "Verifying sources...";
  try {
    const bundle = await api("/api/handoff/gitlab", { method: "POST" });
    setHandoffMessage("Pinned GitLab source integrity verified. Tools and state remain simulated; answer keys await review.");
    await loadHandoffCase(bundle.case.case_id);
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Create GitLab benchmark"; }
}
function renderRehearsal(result) {
  const section = byId("rehearsalResults"); const container = byId("rehearsalTasks");
  section.hidden = false; container.replaceChildren(); byId("rehearsalLimitation").textContent = result.limitation;
  const status = byId("rehearsalState"); status.textContent = result.all_patterns_match ? "All patterns match" : "Pattern mismatch";
  status.dataset.state = result.all_patterns_match ? "complete" : "error";
  result.tasks.forEach((task) => {
    const article = document.createElement("article"); article.className = "matrix-card";
    const head = document.createElement("div"); head.className = "matrix-heading";
    const title = document.createElement("h4"); title.textContent = task.title;
    const diagnosis = document.createElement("span"); diagnosis.className = `cause-badge cause-${task.observed_failure_cause}`;
    diagnosis.textContent = causeLabel(task.observed_failure_cause); head.append(title, diagnosis);
    const grid = document.createElement("div"); grid.className = "matrix-grid";
    task.cells.forEach((cell) => {
      const item = document.createElement("div"); item.className = `matrix-cell ${cell.passed ? "is-pass" : "is-blocked"}`;
      const label = document.createElement("span"); label.textContent = `${cell.corpus_mode} / ${cell.retrieval_mode}`;
      const resultText = document.createElement("strong"); resultText.textContent = cell.passed ? "PASS" : "BLOCKED";
      const detail = document.createElement("small"); detail.textContent = cell.verifier_message;
      item.append(label, resultText, detail); grid.append(item);
    });
    const match = document.createElement("p"); match.className = "matrix-match";
    match.textContent = `Expected ${causeLabel(task.expected_failure_cause)} · ${task.expected_pattern_matches ? "pattern matched" : "pattern mismatch"}`;
    article.append(head, grid, match); container.append(article);
  });
}
async function rehearseHandoff() {
  if (!state.handoffCaseId) return;
  const button = byId("rehearseHandoff"); button.disabled = true; button.textContent = "Rehearsing controls...";
  try {
    const result = await api(`/api/handoff/cases/${encodeURIComponent(state.handoffCaseId)}/rehearse`, { method: "POST" });
    renderRehearsal(result); byId("rehearsalResults").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Run fixture rehearsal"; }
}
function renderAgentExperiment(experiment) {
  const section = byId("agentResults"); const container = byId("agentRunSummary");
  section.hidden = false; container.replaceChildren();
  state.lastAgentExperiment = experiment; state.repairQuestion = null; state.repairAnswer = null; state.repairPatch = null;
  const repair = byId("repairResults");
  const repairable = experiment.expected_pattern_matches && experiment.observed_failure_cause === "corpus_gap";
  repair.hidden = !repairable; byId("repairQuestionStart").hidden = false;
  byId("repairQuestionPanel").hidden = true; byId("approvalPanel").hidden = true;
  byId("replayPanel").hidden = true; byId("replayOutcome").hidden = true;
  byId("repairState").textContent = "Corpus gap isolated"; byId("repairState").dataset.state = "complete";
  const matched = experiment.expected_pattern_matches;
  const status = byId("agentResultState"); status.textContent = matched ? "Pattern matched" : "Pattern mismatch";
  status.dataset.state = matched ? "complete" : "error";
  const diagnosis = document.createElement("p"); diagnosis.className = "agent-diagnosis";
  diagnosis.textContent = `Observed ${causeLabel(experiment.observed_failure_cause)} · expected ${causeLabel(experiment.expected_failure_cause)} · model ${experiment.model}`;
  container.append(diagnosis);
  experiment.runs.forEach((run) => {
    const article = document.createElement("article"); article.className = `agent-run-card is-${run.status}`;
    const head = document.createElement("div"); head.className = "agent-run-heading";
    const title = document.createElement("h4"); title.textContent = `${run.corpus_mode} corpus / ${run.retrieval_mode} retrieval`;
    const runStatus = document.createElement("span"); runStatus.className = "agent-run-status";
    runStatus.textContent = run.status.toUpperCase(); head.append(title, runStatus);
    const facts = document.createElement("p"); facts.className = "agent-run-facts";
    facts.textContent = `Evidence: ${run.retrieved_fact_ids.join(", ") || "none"} · ${run.verifier_message}`;
    const trace = document.createElement("details"); trace.className = "agent-trace";
    const summary = document.createElement("summary"); summary.textContent = `${run.turns.length} model turn${run.turns.length === 1 ? "" : "s"} · ${run.unsupported_action_count} rejected action${run.unsupported_action_count === 1 ? "" : "s"}`;
    const steps = document.createElement("ol");
    run.turns.forEach((turn) => {
      const step = document.createElement("li");
      const decision = document.createElement("strong"); decision.textContent = turn.decision.decision.replaceAll("_", " ");
      const reason = document.createElement("span"); reason.textContent = turn.decision.reason;
      step.append(decision, reason);
      if (turn.decision.tool_id) {
        const tool = document.createElement("code"); tool.textContent = `${turn.decision.tool_id} · citations ${turn.decision.evidence_fact_ids.join(", ") || "none"}`; step.append(tool);
      }
      if (turn.tool_result) {
        const result = document.createElement("small"); result.textContent = `${turn.tool_result.accepted ? "Accepted" : "Rejected"}: ${turn.tool_result.message}`; step.append(result);
      }
      steps.append(step);
    });
    trace.append(summary, steps); article.append(head, facts, trace); container.append(article);
  });
}
async function runHandoffAgent() {
  if (!state.handoffCaseId) return;
  const taskId = byId("agentTaskSelect").value; const button = byId("runHandoffAgent");
  button.disabled = true; button.textContent = "Running four cells...";
  setHandoffMessage("The local model is running four isolated cells. This can take a few minutes.");
  try {
    const result = await api(`/api/handoff/cases/${encodeURIComponent(state.handoffCaseId)}/agent-experiments?task_id=${encodeURIComponent(taskId)}`, { method: "POST" });
    renderAgentExperiment(result); setHandoffMessage("Live successor-agent experiment persisted locally.");
    byId("agentResults").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.textContent = "Run live agent"; updateAgentButton(); }
}
async function createBenchmarkReport() {
  if (!state.handoffCaseId) return;
  const button = byId("createBenchmarkReport"); button.disabled = true; button.textContent = "Aggregating...";
  try {
    const report = await api(`/api/handoff/cases/${encodeURIComponent(state.handoffCaseId)}/benchmark-report`, { method: "POST" });
    const outcome = byId("benchmarkReportOutcome"); outcome.hidden = false; outcome.replaceChildren();
    const title = document.createElement("strong"); title.textContent = `${report.matched_tasks}/${report.total_tasks} causal patterns matched`;
    const detail = document.createElement("p");
    detail.textContent = `Accuracy ${(report.pattern_accuracy * 100).toFixed(0)}% · ${report.model_turns} model turns · ${report.preflight_blocked_cells} preflight blocks · ${report.unsupported_action_count} rejected actions · human review ${report.human_review_complete ? "complete" : "pending"} · ${report.claim_level.replaceAll("_", " ")}`;
    outcome.append(title, detail); outcome.dataset.state = report.matched_tasks === report.total_tasks ? "complete" : "error";
    byId("benchmarkReportState").textContent = report.human_review_complete ? "Benchmark reviewed" : "Mechanism evidence ready";
    byId("handoffPhase").textContent = report.human_review_complete ? "human reviewed benchmark" : (state.reviewPacket ? "independent review pending" : "source benchmark evidence ready");
    await loadHandoffCases();
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Build latest report"; }
}
function renderReviewPacket(response) {
  state.reviewPacket = response.packet; state.reviews = response.reviews;
  const select = byId("reviewTask"); select.replaceChildren();
  response.reviews.forEach((review) => {
    const option = document.createElement("option"); option.value = review.review_id;
    option.textContent = `${review.task_title} · ${review.decision.replaceAll("_", " ")}`;
    select.append(option);
  });
  byId("reviewWorkspace").hidden = false;
  byId("reviewState").textContent = `${response.packet.approved_count}/${response.packet.total_tasks} approved`;
}
async function createReviewPacket() {
  if (!state.handoffCaseId) return;
  const button = byId("createReviewPacket"); button.disabled = true; button.textContent = "Preparing...";
  try {
    const response = await api(`/api/handoff/cases/${encodeURIComponent(state.handoffCaseId)}/review-packet`, { method: "POST" });
    renderReviewPacket(response); setHandoffMessage("Independent review packet is ready. No task has been self-approved.");
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Create review packet"; }
}
async function submitBenchmarkReview() {
  const reviewId = byId("reviewTask").value; const reviewer = byId("reviewerName").value.trim();
  if (!reviewId || !reviewer) { setHandoffMessage("Choose a task and enter the independent reviewer name.", "error"); return; }
  const payload = {
    reviewer, decision: byId("reviewDecision").value, notes: byId("reviewNotes").value,
    checklist: {
      source_alignment: byId("reviewSource").checked,
      start_state_realism: byId("reviewStateCheck").checked,
      reference_actions_complete: byId("reviewActions").checked,
      verifier_criteria_valid: byId("reviewVerifier").checked,
    },
  };
  const button = byId("submitBenchmarkReview"); button.disabled = true; button.textContent = "Recording...";
  try {
    const packet = await api(`/api/handoff/reviews/${encodeURIComponent(reviewId)}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const response = await api(`/api/handoff/cases/${encodeURIComponent(state.handoffCaseId)}/review-packet`, { method: "POST" });
    renderReviewPacket(response);
    const outcome = byId("reviewOutcome"); outcome.hidden = false; outcome.textContent = packet.complete ? "All tasks independently approved." : `Review saved · ${packet.approved_count}/${packet.total_tasks} approved`;
    outcome.dataset.state = packet.complete ? "complete" : "ready";
    await loadHandoffCases();
  } catch (error) { setHandoffMessage(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Record review"; }
}
async function createExpertQuestion() {
  if (!state.lastAgentExperiment) return;
  const button = byId("createExpertQuestion"); button.disabled = true; button.textContent = "Creating...";
  try {
    const response = await api(`/api/handoff/experiments/${encodeURIComponent(state.lastAgentExperiment.experiment_id)}/questions`, { method: "POST" });
    const question = response.questions[0]; state.repairQuestion = question;
    byId("expertQuestionPrompt").textContent = question.prompt;
    byId("expertQuestionMeta").textContent = `Missing fact: ${question.missing_fact_id} · status ${question.status}`;
    byId("repairQuestionStart").hidden = true; byId("repairQuestionPanel").hidden = false;
    byId("repairState").textContent = "Awaiting expert answer";
  } catch (error) { setHandoffMessage(error.message, "error"); button.disabled = false; }
  finally { button.textContent = "Create expert question"; }
}
async function submitExpertAnswer(event) {
  event.preventDefault(); if (!state.repairQuestion) return;
  const button = byId("submitExpertAnswer"); button.disabled = true; button.textContent = "Recording...";
  try {
    const answer = await api(`/api/handoff/questions/${encodeURIComponent(state.repairQuestion.question_id)}/answers`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer_text: byId("expertAnswerText").value, source_reference: byId("expertSource").value, expert_name: byId("expertName").value }),
    });
    state.repairAnswer = answer; byId("expertAnswerForm").querySelectorAll("input, textarea, button").forEach((item) => { item.disabled = true; });
    byId("expertQuestionMeta").textContent = `Missing fact: ${state.repairQuestion.missing_fact_id} · status answered`;
    byId("answerReview").textContent = `${answer.expert_name}: ${answer.answer_text} · source ${answer.source_reference}`;
    byId("approvalPanel").hidden = false; byId("repairState").textContent = "Awaiting owner approval";
  } catch (error) { setHandoffMessage(error.message, "error"); button.disabled = false; }
  finally { button.textContent = "Record answer for review"; }
}
async function approveExpertAnswer() {
  if (!state.repairAnswer) return; const approvedBy = byId("approvedBy").value.trim(); if (!approvedBy) return;
  const button = byId("approveExpertAnswer"); button.disabled = true; button.textContent = "Versioning...";
  try {
    const patch = await api(`/api/handoff/answers/${encodeURIComponent(state.repairAnswer.answer_id)}/approve`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ approved_by: approvedBy }),
    });
    state.repairPatch = patch; byId("handoffCorpus").textContent = patch.new_version_id;
    byId("handoffPhase").textContent = "repair replay ready";
    byId("expertQuestionMeta").textContent = `Missing fact: ${state.repairQuestion.missing_fact_id} · status approved`;
    byId("patchSummary").textContent = `${patch.previous_version_id} → ${patch.new_version_id} · added ${patch.added_fact_ids.join(", ")} · approved by ${patch.approved_by}`;
    byId("replayPanel").hidden = false; byId("repairState").textContent = "Approved—not yet proven";
    await loadHandoffCases();
  } catch (error) { setHandoffMessage(error.message, "error"); button.disabled = false; }
  finally { button.textContent = "Approve and version corpus"; }
}
async function replayPatch() {
  if (!state.repairPatch) return; const button = byId("replayPatch"); button.disabled = true; button.textContent = "Replaying four cells...";
  try {
    const replay = await api(`/api/handoff/patches/${encodeURIComponent(state.repairPatch.patch_id)}/replay`, { method: "POST" });
    const outcome = byId("replayOutcome"); outcome.hidden = false; outcome.replaceChildren();
    const title = document.createElement("strong"); title.textContent = replay.repaired ? "Repair proven" : "Repair not proven";
    const comparison = document.createElement("p"); comparison.textContent = `Before actual/normal: ${replay.before_status.toUpperCase()} · After: ${replay.after_status.toUpperCase()}`;
    outcome.append(title, comparison); outcome.dataset.state = replay.repaired ? "complete" : "error";
    byId("repairState").textContent = replay.repaired ? "Repair validated" : "Replay failed";
    byId("repairState").dataset.state = replay.repaired ? "complete" : "error";
    byId("handoffPhase").textContent = replay.repaired ? "repair validated" : "repair replay failed";
    await loadHandoffCases();
  } catch (error) { setHandoffMessage(error.message, "error"); button.disabled = false; }
  finally { button.textContent = "Replay identical task"; }
}
function renderDocuments(documents) {
  const container = byId("documents"); container.replaceChildren();
  byId("documentCount").textContent = documents.length;
  if (!documents.length) {
    const empty = document.createElement("p"); empty.className = "document-meta";
    empty.textContent = "No documents indexed yet."; container.append(empty); return;
  }
  documents.forEach((info) => {
    const button = document.createElement("button"); button.type = "button"; button.className = "document-item";
    button.addEventListener("click", () => inspectDocument(info.document_id));
    const name = document.createElement("span"); name.className = "document-name"; name.textContent = info.filename;
    const meta = document.createElement("span"); meta.className = "document-meta";
    meta.textContent = `${info.chunks} chunks | ${(info.size_bytes / 1024 / 1024).toFixed(2)} MB`;
    button.append(name, meta); container.append(button);
  });
}
async function loadStatus() {
  try {
    const status = await api("/api/status"); state.status = status;
    const runtime = byId("ollamaState");
    runtime.textContent = status.ollama_ready ? "Runtime ready" : "Runtime unavailable";
    runtime.dataset.state = status.ollama_ready ? "ready" : "error";
    byId("modelState").textContent = `${status.generation_model} | ${status.embedding_model}`;
    byId("dropHint").textContent = `Choose documents up to ${status.max_file_size_mb} MB each`;
    byId("fileInput").accept = status.supported_extensions.join(","); renderDocuments(status.documents); updateAgentButton();
  } catch (error) {
    byId("ollamaState").textContent = "Server unavailable"; byId("ollamaState").dataset.state = "error";
    byId("documents").textContent = error.message;
  }
}
function updateSelection(files) {
  state.selectedFiles = [...files]; byId("ingestButton").disabled = state.selectedFiles.length === 0;
  byId("dropHint").textContent = state.selectedFiles.length
    ? state.selectedFiles.map((file) => file.name).join(", ")
    : `Choose documents up to ${state.status?.max_file_size_mb || 25} MB each`;
  setMessage("");
}
function renderIngestMetrics(metrics, filename) {
  const panel = byId("ingestMetrics"); const list = byId("ingestMetricList");
  panel.hidden = false; list.replaceChildren();
  const rows = [
    ["Document", filename], ["Size", `${metrics.document_size_mb.toFixed(2)} MB`],
    ["Total", duration(metrics.total_seconds)], ["Parsing", duration(metrics.parse_seconds)],
    ["Chunking", duration(metrics.chunk_seconds)], ["Artifact write", duration(metrics.artifact_write_seconds)],
    ["Embedding + index", duration(metrics.embedding_and_index_seconds)], ["Canonical blocks", integer(metrics.canonical_blocks)],
    ["Chunks", integer(metrics.chunks_indexed)], ["Characters embedded", integer(metrics.characters_embedded)],
    ["Throughput", `${metrics.chunks_per_second.toFixed(2)} chunks/s`],
  ];
  rows.forEach(([label, value]) => {
    const row = document.createElement("div"); const term = document.createElement("dt"); const data = document.createElement("dd");
    term.textContent = label; data.textContent = value; row.append(term, data); list.append(row);
  });
}
async function ingestSelected() {
  if (!state.selectedFiles.length) return;
  const button = byId("ingestButton"); button.disabled = true; button.textContent = "Parsing and indexing...";
  setMessage(`Processing ${state.selectedFiles.length} file${state.selectedFiles.length === 1 ? "" : "s"}. Large or scanned files can take longer.`);
  const formData = new FormData(); state.selectedFiles.forEach((file) => formData.append("files", file));
  try {
    const response = await api("/api/documents", { method: "POST", body: formData });
    const successful = response.results.filter((result) => !result.error);
    const failed = response.results.filter((result) => result.error);
    if (successful.length) { const latest = successful.at(-1); renderIngestMetrics(latest.metrics, latest.document.filename); }
    setMessage(`${successful.length} indexed${failed.length ? `, ${failed.length} failed` : ""}.`, failed.length ? "error" : "info");
    state.selectedFiles = []; byId("fileInput").value = ""; await loadStatus();
  } catch (error) { setMessage(error.message, "error"); }
  finally { button.textContent = "Index selected files"; button.disabled = state.selectedFiles.length === 0; }
}
function setMetric(id, value) { byId(id).textContent = value; }
function renderMetrics(metrics) {
  setMetric("endToEnd", duration(metrics.end_to_end_seconds));
  setMetric("tokenRate", `${metrics.output_tokens_per_second.toFixed(1)} tok/s`);
  setMetric("firstToken", duration(metrics.time_to_first_token_seconds));
  setMetric("retrievalTime", duration(metrics.retrieval_seconds)); setMetric("embeddingTime", duration(metrics.query_embedding_seconds));
  setMetric("similarityTime", duration(metrics.similarity_search_seconds)); setMetric("chunksUsed", integer(metrics.retrieved_chunks));
  setMetric("generationTime", duration(metrics.generation_wall_seconds)); setMetric("promptTokens", integer(metrics.prompt_tokens));
  setMetric("outputTokens", integer(metrics.output_tokens)); setMetric("contextSize", `${integer(metrics.context_characters)} chars`);
  setMetric("ollamaTotal", duration(metrics.ollama_total_seconds)); setMetric("modelLoad", duration(metrics.model_load_seconds));
  setMetric("promptEval", duration(metrics.prompt_eval_seconds)); setMetric("generationEval", duration(metrics.generation_eval_seconds));
  setMetric("embeddingModelLoad", duration(metrics.embedding_model_load_seconds)); setMetric("embeddingEval", duration(metrics.embedding_eval_seconds));
  setMetric("embeddingInputTokens", integer(metrics.embedding_input_tokens)); setMetric("embeddingDimensions", integer(metrics.embedding_dimensions));
  const gate = byId("typesafeMetricGroup"); const gateEnabled = metrics.typesafe_candidates > 0;
  gate.hidden = !gateEnabled;
  if (gateEnabled) {
    setMetric("typesafeCandidates", integer(metrics.typesafe_candidates));
    setMetric("typesafeIncluded", integer(metrics.typesafe_included + metrics.typesafe_conflicts));
    setMetric("typesafeReview", integer(metrics.typesafe_review));
    setMetric("typesafeExcluded", integer(metrics.typesafe_excluded));
    setMetric("typesafeTime", duration(metrics.typesafe_wall_seconds));
  }
}
function renderAnswerText(target, answer) {
  const parts = answer.split(/(\[S\d+\])/g);
  parts.forEach((part) => {
    const match = part.match(/^\[(S\d+)\]$/);
    if (!match) { target.append(document.createTextNode(part)); return; }
    const citation = document.createElement("button"); citation.type = "button"; citation.className = "citation-link";
    citation.textContent = part; citation.setAttribute("aria-label", `Open evidence ${match[1]}`);
    citation.addEventListener("click", () => {
      const evidence = document.getElementById(`citation-${match[1]}`);
      if (!evidence) return;
      const details = evidence.querySelector("details"); if (details) details.open = true;
      evidence.scrollIntoView({ behavior: "smooth", block: "center" });
      evidence.classList.add("is-targeted"); window.setTimeout(() => evidence.classList.remove("is-targeted"), 1200);
    });
    target.append(citation);
  });
}
function routeLabel(route) { return route.replaceAll("_", " "); }
function renderEvidenceGate(judgments) {
  if (!judgments?.length) return null;
  const panel = document.createElement("section"); panel.className = "evidence-gate";
  const heading = document.createElement("div"); heading.className = "gate-heading";
  const copy = document.createElement("div"); const kicker = document.createElement("p"); kicker.className = "kicker"; kicker.textContent = "TypeSafe policy";
  const title = document.createElement("h3"); title.textContent = "Evidence gate";
  const policy = document.createElement("code"); policy.textContent = judgments[0].policy_version;
  copy.append(kicker, title); heading.append(copy, policy);
  const counts = { approved: 0, conflict: 0, review: 0, excluded: 0 };
  judgments.forEach((item) => {
    if (item.route === "include") counts.approved += 1;
    else if (item.route === "conflicting_evidence") counts.conflict += 1;
    else if (item.route === "review") counts.review += 1;
    else counts.excluded += 1;
  });
  const summary = document.createElement("div"); summary.className = "gate-summary";
  [["Approved", counts.approved], ["Conflict", counts.conflict], ["Review", counts.review], ["Excluded", counts.excluded]].forEach(([label, value]) => {
    const item = document.createElement("div"); const strong = document.createElement("strong"); const span = document.createElement("span");
    strong.textContent = value; span.textContent = label; item.append(strong, span); summary.append(item);
  });
  const details = document.createElement("details"); details.className = "gate-details";
  const detailsSummary = document.createElement("summary"); detailsSummary.textContent = `Inspect ${judgments.length} candidate decisions`;
  const list = document.createElement("div"); list.className = "gate-list";
  judgments.forEach((item) => {
    const row = document.createElement("article"); row.className = "gate-row";
    const rowTop = document.createElement("div"); rowTop.className = "gate-row-top";
    const source = document.createElement("strong"); source.textContent = `#${item.candidate_rank} · ${item.filename || item.chunk_id}`;
    const badge = document.createElement("span"); badge.className = "route-badge"; badge.dataset.route = item.route; badge.textContent = routeLabel(item.route);
    rowTop.append(source, badge);
    const section = document.createElement("p"); section.textContent = item.section || item.chunk_id;
    const signals = document.createElement("div"); signals.className = "gate-signals";
    [["Relevant", item.is_relevant], ["Evidence", item.contains_answer_evidence], ["Conflict", item.contradicts_query_premise], ["Injection", item.contains_prompt_injection]].forEach(([label, value]) => {
      const signal = document.createElement("span"); signal.textContent = `${label} ${Number(value).toFixed(2)}`; signals.append(signal);
    });
    row.append(rowTop, section, signals); list.append(row);
  });
  details.append(detailsSummary, list); panel.append(heading, summary, details); return panel;
}
function renderAnswer(result) {
  const area = byId("answerArea"); area.replaceChildren();
  const answer = document.createElement("section"); answer.className = "answer-copy";
  const title = document.createElement("h3"); title.textContent = "Answer";
  const copy = document.createElement("div"); renderAnswerText(copy, result.answer); answer.append(title, copy);
  const evidenceHeading = document.createElement("div"); evidenceHeading.className = "evidence-heading";
  const evidenceTitle = document.createElement("h3"); evidenceTitle.textContent = "Retrieved evidence";
  const evidenceNote = document.createElement("p"); evidenceNote.textContent = "Ranked chunks supplied to the local generation model.";
  evidenceHeading.append(evidenceTitle, evidenceNote);
  const evidenceList = document.createElement("div"); evidenceList.className = "evidence-list";
  result.hits.forEach((hit) => {
    const card = document.createElement("article"); card.className = "evidence-card"; card.id = `citation-S${hit.rank}`;
    const top = document.createElement("div"); top.className = "evidence-top";
    const rank = document.createElement("span"); rank.className = "evidence-rank"; rank.textContent = `[S${hit.rank}]`;
    const score = document.createElement("span"); score.className = "evidence-score"; score.textContent = `score ${hit.score.toFixed(4)}`; top.append(rank, score);
    const source = document.createElement("div"); source.className = "evidence-source";
    const pages = hit.chunk.page_numbers.length ? `pages ${hit.chunk.page_numbers.join(", ")}` : "page unknown";
    source.textContent = `${hit.chunk.filename} | ${pages} | ${hit.chunk.section || "section unknown"}`;
    const details = document.createElement("details"); const summary = document.createElement("summary"); summary.textContent = "Show retrieved text";
    const text = document.createElement("p"); text.className = "evidence-text"; text.textContent = hit.chunk.text;
    details.append(summary, text); card.append(top, source, details); evidenceList.append(card);
  });
  const gate = renderEvidenceGate(result.evidence_judgments);
  if (gate) area.append(answer, gate, evidenceHeading, evidenceList);
  else area.append(answer, evidenceHeading, evidenceList);
}
function renderAnswerError(message) {
  const area = byId("answerArea"); area.replaceChildren(); const box = document.createElement("div");
  box.className = "inline-message"; box.dataset.kind = "error"; box.textContent = message; area.append(box);
}
async function askQuestion(event) {
  event.preventDefault(); const question = byId("question").value.trim(); if (!question) return;
  const button = byId("askButton"); button.disabled = true; button.textContent = "Working...";
  byId("traceState").textContent = "Running"; byId("traceState").dataset.state = "running";
  byId("answerArea").innerHTML = '<div class="answer-loading" aria-label="Generating answer"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>';
  try {
    const result = await api("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, top_k: Number(byId("topK").value) }) });
    renderAnswer(result); renderMetrics(result.metrics); byId("traceState").textContent = "Complete"; byId("traceState").dataset.state = "complete";
  } catch (error) { renderAnswerError(error.message); byId("traceState").textContent = "Failed"; byId("traceState").dataset.state = "error"; }
  finally { button.disabled = false; button.textContent = "Ask"; }
}
async function inspectDocument(documentId) {
  try {
    const result = await api(`/api/documents/${encodeURIComponent(documentId)}`);
    byId("dialogTitle").textContent = result.document.filename;
    byId("dialogMeta").textContent = `${result.document.blocks} blocks | ${result.document.chunks} chunks | ${result.document.parser}`;
    const chunks = byId("dialogChunks"); chunks.replaceChildren();
    result.chunks.forEach((chunk) => {
      const item = document.createElement("details"); item.className = "chunk-item";
      const summary = document.createElement("summary"); const pages = chunk.page_numbers.length ? `pages ${chunk.page_numbers.join(", ")}` : "page unknown";
      summary.textContent = `${chunk.chunk_id} | ${pages} | ${chunk.section || "section unknown"}`;
      const text = document.createElement("p"); text.textContent = chunk.text; item.append(summary, text); chunks.append(item);
    }); byId("documentDialog").showModal();
  } catch (error) { setMessage(error.message, "error"); }
}
const dropzone = byId("dropzone");
["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.add("is-dragging"); }));
["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.remove("is-dragging"); }));
dropzone.addEventListener("drop", (event) => updateSelection(event.dataTransfer.files));
byId("fileInput").addEventListener("change", (event) => updateSelection(event.target.files));
byId("ingestButton").addEventListener("click", ingestSelected); byId("refreshButton").addEventListener("click", loadStatus);
byId("questionForm").addEventListener("submit", askQuestion);
byId("question").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); byId("questionForm").requestSubmit(); } });
byId("closeDialog").addEventListener("click", () => byId("documentDialog").close());
byId("documentDialog").addEventListener("click", (event) => { if (event.target === byId("documentDialog")) byId("documentDialog").close(); });
byId("handoffTab").addEventListener("click", () => switchView("handoff"));
byId("ragTab").addEventListener("click", () => switchView("rag"));
byId("initializeHandoff").addEventListener("click", initializeHandoff);
byId("initializeGitlab").addEventListener("click", initializeGitlabBenchmark);
byId("refreshHandoff").addEventListener("click", loadHandoffCases);
byId("rehearseHandoff").addEventListener("click", rehearseHandoff);
byId("runHandoffAgent").addEventListener("click", runHandoffAgent);
byId("createBenchmarkReport").addEventListener("click", createBenchmarkReport);
byId("createReviewPacket").addEventListener("click", createReviewPacket);
byId("submitBenchmarkReview").addEventListener("click", submitBenchmarkReview);
byId("createExpertQuestion").addEventListener("click", createExpertQuestion);
byId("expertAnswerForm").addEventListener("submit", submitExpertAnswer);
byId("approveExpertAnswer").addEventListener("click", approveExpertAnswer);
byId("replayPatch").addEventListener("click", replayPatch);
loadStatus(); loadHandoffCases();
