# Real-world evaluation corpus: GitLab public production runbooks

Date selected: 2026-09-01

## Why this corpus

The original HandoffProof experiment uses a fictional ledger-service handover. That
fixture is useful for proving causal controls safely, but it is not evidence that the
system works on real operational documentation.

The first real-world corpus is a focused subset of GitLab's public production
runbooks. GitLab describes these runbooks as material for stressed on-call engineers
and as a primary source of truth for service maintenance. The repository is licensed
under MIT. The selected files contain real incident workflow, rollback constraints,
Sidekiq architecture, inspection procedures, stuck-queue recovery and concurrency
controls.

## Reproducible source

- Repository: `https://gitlab.com/gitlab-com/runbooks`
- GitLab project ID: `1148549`
- Pinned commit: `4ac275d086328d8e94555ac9ee853c7fb9d66a09`
- License: MIT, included with the local copy
- Local corpus: `data/reference-corpora/gitlab-runbooks-4ac275d`
- Fetch script: `scripts/fetch_gitlab_runbooks_corpus.ps1`

The local `corpus-manifest.json` records the original URL, byte size and SHA-256 hash
of every downloaded file.

## Selected documents

| Document | Operational value |
| --- | --- |
| Root README and LICENSE | Repository purpose, provenance and reuse rights |
| Incident workflow | Escalation, coordination and incident closure constraints |
| GitLab-down procedure | Concrete behavior when normal production systems are unavailable |
| Upgrade and rollback | Approval and database-review gates before rollback |
| Sidekiq service overview | Service ownership and operational context |
| Sidekiq SRE survival guide | Queue, worker, shard and routing-rule mechanics |
| Sidekiq inspection | Evidence-gathering and diagnostic procedures |
| Queue not being processed | Concrete stuck-queue investigation and recovery |
| Sidekiq concurrency limit | Safety controls around worker concurrency |

## Honesty boundary

These source documents are real and publicly maintained. We do not have GitLab's
production access, dashboards, credentials, people or ChatOps tools. Therefore:

- the source corpus is real;
- a test incident and its observed system state will be a disclosed simulation;
- any intentionally omitted page used to create a corpus gap will be a test mutation;
- tool responses and final-state verifiers will remain synthetic and isolated;
- we must not claim that the agent operated GitLab.com or passed GitLab's internal
  acceptance process.

This is substantially stronger than a fully invented corpus while remaining safe and
reproducible. A later organizational pilot would still be required to validate
HandoffProof against a true private team handover.

## Proposed real-world tasks

1. Diagnose why a Sidekiq queue is not being processed and identify the required
   evidence before intervention.
2. Decide whether an application rollback is authorized given incident severity,
   database review and incident-coordination state.
3. Inspect Sidekiq routing and queue state without proposing a mutation first.
4. Change concurrency only when the documented safety conditions and verification
   signals are present.

Before these become benchmark claims, each task needs an explicit start state,
allowlisted synthetic tools, deterministic success criteria and a human-reviewed
answer key derived from the pinned source files.

## Current validation

The eight selected operational Markdown files were run through the real S_RAG
ingestion pipeline on 2026-09-01. All eight parsed successfully and produced 78
embedded chunks in total.

A grounded query asked who must be paged before an application rollback and what
database review or approval is required. Retrieval ranked the `Application Rollback`
section from `upgrade-and-rollback.md` first with a cosine score of `0.7721`. Local
Qwen correctly reported that the IMOC and DBRE on-call must be paged, the DBRE should
review database impact, and IMOC sign-off is required if DBRE review is unavailable.
The response cited the downloaded source chunk.

This validates real-document parsing, embedding, retrieval and grounded generation.
It does not yet validate the Phase 4 successor-agent control matrix against these
documents; building and human-reviewing that real-corpus benchmark is the next gate.
