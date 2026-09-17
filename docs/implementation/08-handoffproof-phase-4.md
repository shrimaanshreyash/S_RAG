# HandoffProof implementation: Phase 4 successor-agent experiment

Date: 2026-09-01

## Outcome

Phase 4 turns the deterministic HandoffProof fixture into an executable local-agent
experiment without giving the model access to the laptop, shell, network or real
services. It keeps the original RAG workbench and the Phase 1–3 fixture rehearsal
available through the same CLI and web application.

This phase answers a narrow technical question: can an evidence-constrained successor
agent complete a representative handover task, and can controlled counterfactuals
separate a corpus gap from a retrieval gap or an agent/tool gap?

Expert answers, approved corpus patches and repaired-task replay were subsequently
implemented in Phase 5 and are documented in
[`10-handoffproof-phase-5.md`](10-handoffproof-phase-5.md).

## How one experiment works

The selected task is run in four fresh, isolated environments:

| Corpus | Retrieval | Purpose |
| --- | --- | --- |
| Actual | Normal | Reproduce what the successor would experience |
| Actual | Oracle | Test whether perfect retrieval can rescue the current corpus |
| Complete | Normal | Test whether adding the missing fact is enough through normal retrieval |
| Complete | Oracle | Test the agent and tool when all required evidence is directly supplied |

The resulting pass/block pattern is classified as:

- **supported control** — all four cells pass;
- **corpus gap** — the actual corpus cannot pass even with oracle retrieval, while
  the complete corpus can;
- **retrieval gap** — oracle retrieval passes but normal retrieval misses the needed
  fact;
- **agent/tool gap** — even complete corpus plus oracle retrieval cannot pass.

If Ollama or another runtime dependency fails, the experiment aborts with an error.
Runtime failure is not converted into an agent/tool diagnosis.

## Evidence and action boundary

The local model receives:

- the task objective and success criteria;
- the facts returned for that one experimental cell;
- the current synthetic task state;
- an explicit allowlist of tools and argument descriptions;
- previous decisions and tool observations from the same cell.

Before any mutating tool can run, the application checks that the model cited the
exact fact IDs required by that tool and that those facts were actually included in
the retrieved context. The tool then validates arguments again. Rejected actions are
recorded in the trace.

All task tools operate on an in-memory synthetic state. They cannot invoke a shell,
call a network endpoint, read credentials or change a real service. A fresh sandbox
is created for every cell, and a deterministic verifier decides success from its
final state.

## Retrieval reuse

Normal retrieval reuses the baseline Ollama embedder and local cosine index. Oracle
retrieval is deliberately non-semantic: it supplies the task's required facts when
they exist in the selected corpus. The seeded retrieval-gap fact is excluded from
the normal retrieval surface, so the experiment tests a controlled fault instead of
hoping an embedding model happens to miss it.

## Persistent traces

Each cell run stores inspectable JSON below `artifacts/handoffproof/runs`. A trace
contains:

- corpus and retrieval modes;
- retrieved fact IDs;
- every structured model decision and citation;
- evidence-gate and tool results;
- model latency and token counts;
- final synthetic state;
- deterministic verifier message and status.

The four-cell experiment summary is stored below
`artifacts/handoffproof/experiments`. Existing case data remains below
`artifacts/handoffproof/cases`.

## Terminal access

```powershell
uv run srag handoff init-demo
uv run srag handoff run --task task-control-queue
uv run srag handoff runs
uv run srag handoff inspect-run <run_id>
```

The other task IDs are:

- `task-corpus-gap-rollback`
- `task-retrieval-gap-phoenix`
- `task-agent-gap-key-rotation`

`run` executes the selected task through all four cells using the configured local
Ollama model. `rehearse` remains the fast deterministic wiring check and must not be
described as an agent result.

## Web access

Run `uv run srag serve`, open `http://127.0.0.1:8765`, and choose HandoffProof. The
workbench provides a task selector and a **Run live agent** action. It displays the
observed/expected diagnosis, each cell's evidence and verifier outcome, and an
expandable decision/tool trace. The action remains disabled when the status endpoint
reports Ollama unavailable.

## Acceptance criteria

Phase 4 is complete when:

1. controlled tests make all four seeded diagnoses observable through real
   orchestration rather than the fixture classifier alone;
2. actions without retrieved required evidence are rejected;
3. all four cells are isolated and persist inspectable traces;
4. CLI and web APIs expose the same service-layer behavior;
5. the original RAG and fixture-rehearsal workflows remain available;
6. linting, strict type checking, automated tests, JavaScript syntax and real browser
   checks pass;
7. any unavailable local-model runtime is reported honestly as a runtime limitation.

## Verification status

The Phase 4 implementation passed Ruff formatting/linting, strict mypy across 22
source files, all 13 automated tests and browser JavaScript syntax on 2026-09-01.
Controlled successor-agent tests ran all four tasks through all four cells (16
persisted cell runs), matched every expected diagnosis and exercised evidence-gate
rejection. The persisted terminal fixture still matched all four seeded patterns.

A real Playwright session verified the Phase 1–4 web view, task selector, offline
live-button gate, fixture matrices, RAG-baseline switch and 390 × 844 responsive
layout with zero console errors or warnings. The captured offline-state evidence is
`output/playwright/handoffproof-phase-4-offline.png`.

The local Ollama endpoint refused the connection during this verification, so no
live Qwen experiment is claimed. The code and controlled orchestration are complete;
one live four-cell model trial remains the runtime acceptance check when Ollama is
available.
