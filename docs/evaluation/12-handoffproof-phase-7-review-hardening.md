# HandoffProof Phase 7: Review and benchmark hardening

Date: 2026-09-15

## Goal

Phase 7 makes the Phase 6 result more credible and cheaper to reproduce. It does not
add another showcase feature. It addresses the observed failure mode in the retained
Phase 6 traces: Qwen repeatedly invented tool aliases or retried actions after a cell
was already known to be impossible.

## Feasibility preflight

Each cell now checks two controlled prerequisites before model inference:

1. every task-required fact is present in the retrieved evidence; and
2. every task-required tool exists in the bounded environment.

When either prerequisite is absent, the runner persists one `stop_blocked` turn with
`decision_source=orchestrator_preflight`, the exact missing facts or tools, and a gate
message explaining why the model was not called. These turns remain visible in JSON,
terminal inspection and the browser trace. They are not counted as model decisions.

Cells that can satisfy the task still use the local `qwen3:4b` model. The prompt now
includes exact required fact and tool IDs, prohibits tool aliases, and prohibits
repeating an identical rejected action.

## Live before-and-after result

The final Phase 7 report is `7bc6e196f4634980af9db4754fd464bb`. It compares against the
latest retained Phase 6 report and records:

| Measure | Phase 6 | Phase 7 | Change |
| --- | ---: | ---: | ---: |
| Causal patterns matched | 4/4 | 4/4 | unchanged |
| Total trace steps | 79 | 28 | -51 |
| Actual model turns | 79 | 20 | -59 |
| Rejected actions | 55 | 0 | -55 |
| Preflight-blocked cells | 0 | 8 | +8 explicit blocks |

The new experiment IDs are:

- supported control: `1b7e5ce2928f48aa91906efef97532dd`;
- corpus gap: `0420fefaf0d74e359abb397c666718a8`;
- retrieval gap: `f1dcaef3389e48c588116099bdce59d5`;
- agent/tool gap: `ec64db7b70734736afdcb15198551827`.

This improvement is an orchestration result, not evidence that the model became more
capable. The system stopped asking the model to solve cells that the controlled test
definition already proves impossible.

## Independent review workflow

The terminal and browser interfaces can create a persistent review packet with one
item per benchmark task. Approval requires a named reviewer to confirm:

- source alignment;
- realistic simulated start state;
- complete reference actions; and
- valid verifier criteria.

A partial checklist cannot produce an approval. The case changes to
`human_reviewed` only after all four task reviews are approved. The initial Phase 7
packet is `dbb3c701ea2b46baa1c47a95eca95c1e` and remains deliberately 0/4 pending.
The project authors did not impersonate an independent reviewer.

## Access

```powershell
uv run srag handoff benchmark-report gitlab-runbooks-handover-benchmark
uv run srag handoff review-packet gitlab-runbooks-handover-benchmark
uv run srag handoff reviews --case gitlab-runbooks-handover-benchmark
uv run srag handoff review-task <review_id> --by "Reviewer" --decision approved --confirm-all
uv run srag serve
```

## Verification and claim boundary

Ruff, strict mypy, JavaScript syntax validation and all 26 automated tests pass. Tests
cover model-free preflight blocking, source tamper rejection, evidence-gated tools,
review packet persistence, and refusal of partial approvals.

The desktop and 390 x 844 responsive browser flows were checked with zero console
errors or warnings after a clean reload. The retained public screenshot is stored at
`output/playwright/handoffproof-phase-7-review-hardening.png`.

The current claim remains `source_derived_mechanism_evidence_only`. Source integrity
is verified and the causal mechanisms execute locally, but the task interpretations
and answer keys have not been independently reviewed by a human, and no GitLab
production system was used. A private organizational pilot would still be required to
claim real handover readiness.

## External agent review update

A separate Gemini 3.8 Flash agent subsequently completed the repository's adversarial
review protocol. It reported all four task designs passing source alignment,
start-state realism, reference-action completeness and verifier validity, while
retaining the source-derived claim boundary. It also found a Windows PowerShell 5.1
UTF-8 BOM incompatibility in corpus initialization. The writer, loader and regression
coverage were corrected. In a focused follow-up from a clean checkout at commit
`fd06527`, the same reviewer reported that Windows PowerShell 5.1 produced a BOM-free
manifest, initialization succeeded without a workaround, and all 37 tests passed.
The independent-agent evidence is therefore recorded as
`independent_agent_review_complete`.

This is independent agent evidence, not independent human review. Details and the
remediation boundary are recorded in
[`15-independent-agent-review.md`](15-independent-agent-review.md).
