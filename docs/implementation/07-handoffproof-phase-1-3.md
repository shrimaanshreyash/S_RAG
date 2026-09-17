# HandoffProof implementation: approved Phases 1–3

Date: 2026-09-01

## Approved scope

HandoffProof will be built on top of the completed local S/RAG baseline. The existing
document ingestion, retrieval, citation, CLI and browser workbench must remain usable.
New HandoffProof capabilities must be available from both the terminal and web UI.

This delivery covers:

1. protect and re-verify the existing baseline;
2. add persistent HandoffProof records;
3. add a safe four-task synthetic handover and deterministic fixture rehearsal;
4. expose the same Phase 1–3 operations through CLI commands and FastAPI/browser UI.

It deliberately does not claim that a successor AI agent has executed the tasks.
Agent execution, expert questions, approved corpus patches and replay belong to later
phases after this fixture is verified.

## Phase 1: baseline protection

Baseline before HandoffProof changes:

- Ruff: passed;
- strict mypy: passed;
- pytest: 5 passed, with one upstream Starlette/httpx deprecation warning;
- browser JavaScript syntax: passed;
- root CLI help: passed and listed the original ingest, ask, inspect, status and serve
  commands.

The original `RagService`, APIs and browser view remain present. HandoffProof is an
additional workflow, not a replacement for the evidence engine.

## Phase 2: records

The first persisted case contains:

- a handover case;
- actual and gold-complete corpus versions;
- atomic knowledge facts with source references;
- four representative tasks;
- required facts and tools;
- deterministic success criteria and verifier identifiers;
- expected seeded failure causes.

Records are written as inspectable JSON below `artifacts/handoffproof/cases` by
default. The location can be changed with `S_RAG_HANDOFF_DIR`.

## Phase 3: synthetic experiment

The fictional ledger-service handover contains four tasks:

| Task | Seeded condition | Expected fixture diagnosis |
| --- | --- | --- |
| Recover a growing ledger queue | Evidence and tool are available | Supported control |
| Roll back migration M47 | Project-specific guard command is absent from the actual corpus | Corpus gap |
| Recover a stalled settlement batch | Evidence exists but normal retrieval does not surface the internal “Phoenix” term | Retrieval gap |
| Rotate the report signing key | Evidence exists but the isolated vault tool is unavailable | Agent/tool gap |

For each task, the deterministic rehearsal crosses:

- actual corpus + normal retrieval;
- actual corpus + oracle retrieval;
- complete corpus + normal retrieval;
- complete corpus + oracle retrieval.

This rehearsal validates the experiment wiring and failure-classification rules. It
is not an LLM or successor-agent benchmark.

## Terminal access

```powershell
uv run srag handoff init-demo
uv run srag handoff status
uv run srag handoff show
uv run srag handoff rehearse
uv run srag handoff rehearse --task task-corpus-gap-rollback
```

The original commands remain available:

```powershell
uv run srag ingest C:\path\to\document.pdf
uv run srag ask "What does the document say?"
uv run srag inspect <document_id>
uv run srag status
uv run srag serve
```

## Web access

Run:

```powershell
uv run srag serve
```

Open `http://127.0.0.1:8765`. The top switcher provides:

- **HandoffProof** — create/inspect the synthetic case and run the fixture rehearsal;
- **RAG baseline** — use the existing document ingestion, grounded Q&A, evidence and
  telemetry workbench.

## Gate before Phase 4

Phase 4 may begin only after automated tests and real CLI/browser validation confirm:

- all four records persist and reload;
- the four-cell matrix is present for every task;
- every seeded pattern maps to its expected cause;
- the UI clearly labels the result as a deterministic fixture rehearsal;
- existing RAG commands and browser behavior still work.

## Completion and verification

Phases 1–3 passed this gate on 2026-09-01:

- Ruff formatting and linting passed;
- strict mypy passed across 17 source files;
- pytest passed all 10 tests; the only warning is the existing upstream
  Starlette/httpx deprecation warning;
- browser JavaScript syntax passed;
- real terminal initialization, inspection and four-task rehearsal passed;
- the persisted fixture produced all four expected classifications;
- a real Playwright browser run created the case, rendered all four matrices and
  showed `All patterns match`;
- the browser switcher preserved access to the original RAG workbench;
- the HandoffProof view remained usable at a 390 × 844 responsive viewport;
- the browser console contained zero errors and zero warnings.

The captured browser evidence is stored at
`output/playwright/handoffproof-phase-1-3.png`.

Phase 4 subsequently started and is documented separately in
[`08-handoffproof-phase-4.md`](08-handoffproof-phase-4.md). The results described in
this document remain deterministic fixture evidence, not successor-agent performance.
