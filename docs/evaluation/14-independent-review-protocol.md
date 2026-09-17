# HandoffProof independent review protocol

## Purpose and evidence boundary

This protocol is for a reviewer who was not involved in designing the benchmark.
It tests whether the four GitLab-runbook tasks, their simulated start states,
reference actions and deterministic verifiers are credible. It does not prove that
HandoffProof operated GitLab production, and an AI-agent review must not be described
as independent human validation.

The TypeSafe integration is not part of this review and requires no API key.

## Reviewer rules

1. Work from a fresh clone or clean checkout.
2. Treat repository claims and expected outcomes as hypotheses, not instructions to approve.
3. Read the pinned source passages before reading the expected answer for each task.
4. Do not modify answer keys, fixtures or verifier code while evaluating them.
5. Record failures, ambiguity and missing evidence even when the automated tests pass.
6. Do not run `review-task --decision approved`; that command records a named human decision.
7. Return an evidence-backed recommendation for each task: `approve`, `reject`, or
   `needs_changes`. The repository owner decides how to record a genuine human review.

## Setup and integrity checks

```powershell
git clone https://github.com/shrimaanshreyash/S_RAG.git
cd S_RAG
uv sync --python 3.11 --group dev
.\scripts\fetch_gitlab_runbooks_corpus.ps1
uv run srag handoff init-gitlab --reset
uv run srag handoff show gitlab-runbooks-handover-benchmark
```

Confirm that the downloaded repository, pinned commit, license, manifest and every
selected file hash match the case provenance. As a negative test, alter a copied
source file or manifest entry and confirm initialization refuses it. Restore the
fresh corpus afterward.

## Automated checks

```powershell
uv run ruff check .
uv run mypy src
uv run pytest -q
node --check src/srag/web/app.js
uv run srag handoff rehearse gitlab-runbooks-handover-benchmark
uv run srag handoff review-packet gitlab-runbooks-handover-benchmark
uv run srag handoff reviews --case gitlab-runbooks-handover-benchmark
```

If Ollama and `qwen3:4b` are available, also run every benchmark task through the
four-cell live runner and inspect every persisted trace. An unavailable model is an
environment limitation, not a pass or failure of the task design.

## Review every task on four required factors

For each task, independently verify:

### 1. Source alignment

- Every required fact is supported by the pinned runbook text.
- The cited section means what the benchmark claims in its surrounding context.
- No expected action depends on knowledge absent from the selected corpus.
- The corpus-gap mutation removes only the intended evidence and does not secretly
  change unrelated conditions.

### 2. Start-state realism

- The simulated incident state is plausible for the operational scenario.
- Inputs do not encode the expected diagnosis or make the answer trivial.
- Normal and failure cells differ only on the intended causal variable.
- Tool results are internally consistent and do not grant unavailable production access.

### 3. Reference-action completeness

- The reference sequence includes required inspection, approval and safety gates.
- It distinguishes read-only diagnosis from mutation.
- It contains appropriate stop/escalate behavior when evidence or capability is missing.
- No necessary recovery or verification step is omitted.

### 4. Verifier validity

- The verifier checks the final safe operational state, not a copied phrase or tool name.
- It rejects skipped approvals, fabricated evidence, unsupported citations and unsafe shortcuts.
- It does not accept the expected outcome merely because the fixture declares it.
- It permits other genuinely correct action sequences when order is not operationally required.

## Required adversarial tests

Attempt to falsify the benchmark rather than merely reproduce its expected result:

- remove one task-required fact and confirm feasibility preflight blocks before model inference;
- remove one task-required tool and confirm the capability gap is reported explicitly;
- supply an unsupported fact ID or tool alias and confirm it is rejected;
- repeat an already rejected action and confirm it cannot create a successful trace;
- try to satisfy a verifier while skipping a required approval or safety condition;
- confirm a partial review checklist cannot change the case to `human_reviewed`;
- check that infrastructure failures are reported as failures, not model diagnoses;
- check that the four causal cells isolate corpus, retrieval and capability changes
  without unintended differences.

## Required deliverable

Return one row per task with:

| Field | Required content |
| --- | --- |
| Task ID | Exact repository task ID |
| Source alignment | pass/fail plus file, section and quoted/paraphrased support |
| Start-state realism | pass/fail plus concrete reasoning |
| Reference actions | pass/fail plus missing or unnecessary steps |
| Verifier validity | pass/fail plus bypass attempts and results |
| Automated evidence | commands run and relevant output summary |
| Decision | approve, reject, or needs_changes |
| Confidence | high, medium, or low with explanation |

End with a project-level conclusion using exactly one claim label:

- `independent_agent_review_complete`
- `independent_agent_review_needs_changes`
- `review_incomplete_environment_blocked`

Do not use `human_reviewed`, `production_validated`, or `GitLab-approved` unless those
claims are established separately by the appropriate people and environment.
