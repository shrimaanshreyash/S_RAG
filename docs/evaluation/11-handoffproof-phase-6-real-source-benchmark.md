# HandoffProof Phase 6: real-source handover benchmark

Date: 2026-09-09

## Outcome

Phase 6 moves HandoffProof from a fully fictional handover fixture to a reproducible,
source-derived benchmark. The knowledge comes from GitLab's public production
runbooks; the incident state, tools, and verifiers remain disclosed local
simulations.

This is **source-derived mechanism evidence**, not a claim that HandoffProof operated
GitLab.com or passed GitLab's internal acceptance process. The answer keys remain
`source_derived_review_pending` until an independent human reviewer accepts them.

## Provenance and integrity gate

`srag handoff init-gitlab` refuses to create the case unless all of these checks pass:

- repository equals `https://gitlab.com/gitlab-com/runbooks`;
- commit equals `4ac275d086328d8e94555ac9ee853c7fb9d66a09`;
- license metadata equals MIT;
- four operational source files exist;
- manifest SHA-256 and recomputed file SHA-256 match the pinned expected hashes.

Every executable knowledge fact stores its source path, source anchor, commit,
SHA-256, and review status. A modified source file is rejected before the benchmark
case can be persisted.

## Source-derived causal tasks

| Task | Pinned runbook basis | Seeded control |
| --- | --- | --- |
| Investigate an unprocessed Sidekiq queue | Queue metrics plus Chef and Kubernetes scheduling checks | Supported control |
| Authorize a simulated GitLab.com rollback | Incident record, IMOC/DBRE paging, database review, and Delivery handoff | Corpus gap |
| Inspect the longest-running Sidekiq job | Read-only Rails console and `Sidekiq::Workers` inspection | Retrieval gap |
| Relieve a simulated concurrency-limit backlog | Rate comparison, temporary disablement, drain monitoring, restoration, and follow-up | Agent/tool gap |

The actual corpus intentionally omits the rollback procedure. Normal retrieval
intentionally misses the runtime-inspection procedure. The concurrency mutation tool
is intentionally unavailable. These mutations are benchmark controls, not defects in
the downloaded source corpus.

## Safety boundary

The successor agent receives only curated source-derived facts, a fresh simulated
state, and allowlisted in-memory tools. No tool calls a shell, GitLab API, ChatOps,
PagerDuty, database, Redis, Kubernetes, Chef, or production service.

Source-dependent read-only tools also require their exact retrieved fact ID. This is
not an operational authorization policy; it prevents tool names from leaking the
missing procedure and invalidating the retrieval-gap experiment. Mutating tools keep
the same citation and argument gates established in Phase 4.

## Live local-Qwen evidence

Local `qwen3:4b` ran every task across actual/complete corpus and normal/oracle
retrieval cells. The latest valid experiment for each task matched its expected
cause:

- supported control: `5b8add68440547f5a2eba424d287bd53`;
- corpus gap: `4e1e7e2cddc24d0aa4f6f0c450615587`;
- retrieval gap: `98d7f387ed524372a2036af9cc607f6d`;
- agent/tool gap: `f9e6f9e2313448ae886d824500a95fa2`.

Persisted report `f487a51fe5b4425caa035b79444463ab` records:

- causal pattern accuracy: 4/4 (100%);
- source integrity: verified;
- human review: pending;
- claim level: `source_derived_mechanism_evidence_only`;
- 79 total model turns and 55 rejected actions.

The high rejected-action count is retained rather than hidden. It shows that a small
local model often retries actions after evidence or capability rejection even when
the aggregate causal diagnosis remains correct.

## Defect found during validation

The first retrieval-gap live run, `b02d48f287c5481993d4e51e9583b932`, was invalid:
read-only tool names exposed enough of the procedure for the model to act without the
missing fact. The run produced a pattern mismatch and is preserved in the evidence
store.

The gate was corrected so every source-dependent tool declares required fact IDs.
The replacement run then produced the intended retrieval-gap pattern. Automated
tests now reject both tampered source files and uncited source-dependent diagnostic
actions.

## Access

```powershell
uv run srag handoff init-gitlab
uv run srag handoff show gitlab-runbooks-handover-benchmark
uv run srag handoff rehearse gitlab-runbooks-handover-benchmark
uv run srag handoff run gitlab-runbooks-handover-benchmark --task <task_id>
uv run srag handoff benchmark-report gitlab-runbooks-handover-benchmark
uv run srag serve
```

The browser can initialize the GitLab benchmark, inspect provenance and review
status, rehearse all four controls, run any one live task, and aggregate the latest
four live experiments into the same report.

## Verification

The completed Phase 6 implementation passed Ruff formatting and linting, strict
mypy, JavaScript syntax validation, and all 23 automated tests. A real browser run
verified initialization, provenance labeling, the deterministic four-task matrix,
the persisted 4/4 report, and the 390 x 844 responsive layout with zero console
errors or warnings. The full-page evidence is stored at
`output/playwright/handoffproof-phase-6-real-source-benchmark.png`.

## Remaining gate

An independent reviewer still needs to confirm each task's fact interpretation,
starting state, reference sequence, and verifier criteria. Only after that explicit
review should `benchmark_status` move to `human_reviewed`. A private organizational
pilot would still be necessary for any claim about real handover readiness.

A later external agent review is recorded in
[`15-independent-agent-review.md`](15-independent-agent-review.md). It adds adversarial
agent-review evidence but does not replace the human-review requirement above.
