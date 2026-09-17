# TypeSafe evidence governor: Phase 0 integration

## Status

Implemented and exercised in the private local workspace. The API key is stored only
in the ignored local `.env`. The committed example remains off by default so a fresh
checkout never attempts a preview API call without the operator deliberately enabling it.

## Purpose

Jev is used as a typed semantic judgment layer, not as the answer generator and not
as a safety authority. For each query/passage pair it returns four probabilities in
one request:

1. `is_relevant`
2. `contains_answer_evidence`
3. `contradicts_query_premise`
4. `contains_prompt_injection`

The application retains the raw probabilities and applies an explicit routing policy
in Python. Only `include` and `conflicting_evidence` passages reach local Qwen.
Ambiguous passages are held for review; injection, irrelevant and weak passages are
excluded. Conflict labels are preserved in the final context so Qwen can challenge a
false premise instead of silently accepting it.

## Evidence boundary

- Type correctness guarantees the response shape, not factual correctness.
- The current thresholds are explicit project defaults adapted from TypeSafe's
  published RAG cookbook, not validated production defaults.
- Prompt-injection scoring is an additional filter, not a security boundary. Source
  text remains untrusted throughout the pipeline.
- Deterministic HandoffProof prerequisites, action gates and task verifiers remain
  authoritative.
- Initial live testing uses only public sample text and the pinned public GitLab
  runbooks. Do not upload confidential, regulated or customer material during the
  preview evaluation.
- Do not publish TypeSafe benchmark or performance results under the supplied terms
  without written authorization or confirmed replacement terms.

## Configuration

The real key belongs in `C:\S_RAG\.env`, which is ignored by Git:

```dotenv
TYPESAFE_API_KEY=replace_with_the_console_key
S_RAG_TYPESAFE_ENABLED=false
S_RAG_TYPESAFE_MODEL=jev-latest
S_RAG_TYPESAFE_CANDIDATE_TOP_K=12
S_RAG_TYPESAFE_MAX_WORKERS=4
S_RAG_TYPESAFE_TIMEOUT_SECONDS=30
```

Keep the RAG switch false for the first probe:

```powershell
uv run srag typesafe status
uv run srag typesafe probe
```

The probe sends one public, non-sensitive query/passage pair, prints all four raw
probabilities, the code-selected route, actual model, latency and token usage.

## Calibration gate

Before enabling the governor for normal RAG queries:

1. Create a labeled set containing relevant evidence, near misses, false premises,
   contradictions, weak evidence and planted prompt injections.
2. Record the exact model alias/version returned by the API.
3. Measure each raw judgment against the labels.
4. Select routing thresholds from the labeled outcomes and consequence of each error.
5. Freeze the policy version and add regression cases.
6. Compare the same RAG questions with the governor disabled and enabled.

The evaluation should report passage precision/recall, false exclusions, missed
injections, contradiction detection, review rate, final citation support, latency,
input tokens and cost. Results are internal evaluation evidence until the agreement
allows publication.

### Private evaluation boundary

The policy was evaluated locally using labeled controls, repeated calls and
source-derived passages. The harnesses, fixtures, raw probabilities and measured
outcomes are deliberately excluded from the public repository. Anyone enabling the
integration should build a representative private set for their own corpus and keep
claims within the terms governing their TypeSafe access.

Policy v4 separates two decisions by design:

- relevance asks whether the passage concerns the same specific operational subject;
- answer evidence asks whether it contains a concrete fact, rule, condition or procedure
  that directly helps answer the request.

The evidence judge uses a bounded worker pool. Result ordering remains the retrieval
ordering, and only independent per-passage calls overlap.

### Retrieval and UI integration

When the governor is enabled, retrieval first supplies the configured candidate pool
to TypeSafe even if the user requests fewer final sources. After routing, the application
returns at most the user's requested source count. This allows strong lower-ranked
evidence to replace weak high-ranked chunks instead of being hidden before judgment.

The local web workbench displays an Evidence Gate panel with the active policy, route
totals, every candidate decision and its four probabilities. The trace panel also shows
candidate count, approved/review/excluded totals and gate time. This is operator-facing
audit evidence; it is not a claim that the preview system is a production safety boundary.

## Publication boundary

- A future public repository may show the optional integration code, with TypeSafe off
  by default and no credentials or private reports.
- The repository does not grant TypeSafe access. Running the TypeSafe path requires the
  user's own authorized early-access account and API key.
- Do not publish preview benchmark results, raw probability reports, latency/cost
  comparisons or performance claims without TypeSafe's written permission or updated
  governing terms.
- Experimental benchmark harnesses and fixtures are excluded from the public branch.
- Do not host this as a third-party TypeSafe-backed service while access is limited to
  evaluation under the supplied agreement.

## Implemented files

- `src/srag/typesafe_evidence.py`: questions, raw judgments and routing policy
- `src/srag/config.py`: feature switch, key, model, candidate count, workers and timeout
- `src/srag/service.py`: optional retrieval-to-generation integration
- `src/srag/generation.py`: conflict labels in the local-Qwen evidence context
- `src/srag/cli.py`: status and small public-sample probe commands
- `src/srag/web/`: visible evidence-gate audit panel and telemetry
- `tests/test_typesafe_evidence.py`: simulated SDK responses and routing checks
- `tests/test_service_typesafe.py`: candidate-pool, final-limit and disabled-path checks
