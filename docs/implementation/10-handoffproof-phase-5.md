# HandoffProof implementation: Phase 5 expert-approved repair

Date: 2026-09-01

## Outcome

Phase 5 closes the loop between a proven handover failure and an auditable corpus
repair. It does not let the agent invent missing documentation and does not let an
unreviewed expert answer silently enter retrieval.

The complete flow is:

```text
live four-cell experiment
  -> isolated corpus gap only
  -> precise question for one missing fact
  -> expert answer recorded as pending
  -> separate named-owner approval
  -> new immutable approved corpus version
  -> identical task and verifier replayed
  -> before/after actual-normal proof
```

Retrieval gaps and agent/tool gaps are rejected before a question is created. Runtime
errors also remain infrastructure failures rather than repair candidates.

## Persistent records

Phase 5 adds inspectable JSON records below `artifacts/handoffproof`:

- `questions` — task, source experiment, missing fact and question status;
- `answers` — exact answer, source reference, expert identity and approval status;
- `patches` — previous/new corpus versions, added fact and approving owner;
- `replays` — source/replay experiment IDs and before/after run IDs.

Corpus versions contain explicit fact-ID membership. Retrieval now derives the actual
corpus from the case's current version rather than a mutable global flag. Previous
versions therefore preserve which facts were approved at that point in time.

## Approval boundary

Submitting an answer changes only the question and answer records. Approval is a
separate operation requiring an approver name. It:

1. verifies the question is awaiting approval;
2. verifies the missing fact is not already in the approved corpus;
3. records the answer text and source as the approved fact;
4. creates a new corpus version without changing the preceding version;
5. records the patch and moves the case to `repair_replay_ready`.

Approval does not claim the repair works. Only replay can move the case to
`repair_validated`.

## Terminal access

```powershell
uv run srag handoff ask-expert <experiment_id>
uv run srag handoff questions
uv run srag handoff answer <question_id> --text "..." --source "..." --expert "..."
uv run srag handoff approve <answer_id> --by "..."
uv run srag handoff replay <patch_id>
```

The browser provides the same staged flow after a live experiment matches the corpus
gap pattern. The pending answer, approval boundary, version transition and replay
result remain visible as separate states.

## Controlled verification

Automated tests verify that:

- only isolated corpus gaps can create questions;
- submitting an answer leaves the current corpus version unchanged;
- approval adds exactly the missing fact to a new version;
- replay uses the original task and deterministic verifier;
- before is blocked, after passes and the repair is marked proven;
- missing API records return 404 while runtime failures remain 503.

## Live local-Qwen evidence

The initial live run exposed two protocol defects: the structured output ceiling was
too small, and verbose prior-turn history caused Qwen to anchor on an obsolete state.
The decision budget was raised to 768 tokens, evidence-array instructions were made
explicit, and history was reduced to compact tool outcomes while current state was
declared authoritative.

After those corrections, local `qwen3:4b` produced the expected corpus-gap pattern:

- source experiment: `d5f23882c9ca4f7c8b5bc2bd3338503f`;
- actual/normal and actual/oracle did not pass;
- complete/normal and complete/oracle passed;
- observed and expected diagnosis both equaled `corpus_gap`.

The synthetic fixture repair then recorded:

- patch: `1ce7f003c6b34b23b7f7d85e8cfeecc8`;
- new corpus version: `actual-repair-1ce7f003`;
- replay: `6406c6de782747afb62944a7f8cd7c3d`;
- before actual/normal: failed after exhausting rejected actions;
- after actual/normal: passed;
- repair proven: yes.

The expert and owner identities in this validation are explicitly named `Synthetic
Fixture Expert` and `Synthetic Fixture Owner`; they are not real organizational
approvals.

## Browser verification

A separate temporary case completed the same live flow through the web interface.
The UI showed the matched Phase 4 diagnosis, expert question, pending answer,
independent approval, corpus version transition and the exact `FAILED -> PASSED`
repair proof.
It remained usable at a 390 × 844 viewport and produced zero console errors or
warnings. Browser evidence is stored at
`output/playwright/handoffproof-phase-5-repair.png`.

## Remaining real-world gate

The GitLab runbooks corpus is real, pinned and successfully indexed, but its agent
tasks, safe tools, scenario states and verifier answer keys still require human
review. Phase 5 proves the repair mechanism with a live model on a synthetic service;
it does not yet claim a real GitLab operational handover was repaired.
