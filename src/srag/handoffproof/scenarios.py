from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from srag.handoffproof.domain import (
    BenchmarkStatus,
    CorpusVersion,
    FailureCause,
    HandoffCase,
    HandoffCaseBundle,
    KnowledgeFact,
    SourceProvenance,
    TaskDefinition,
)

SYNTHETIC_CASE_ID = "synthetic-ledger-service-handover"
GITLAB_CASE_ID = "gitlab-runbooks-handover-benchmark"
GITLAB_CORPUS_DIRNAME = "gitlab-runbooks-4ac275d"
GITLAB_REPOSITORY = "https://gitlab.com/gitlab-com/runbooks"
GITLAB_COMMIT = "4ac275d086328d8e94555ac9ee853c7fb9d66a09"
GITLAB_SOURCE_HASHES = {
    "docs/sidekiq/sidekiq-queue-not-being-processed.md": (
        "f6d6df78198ea1859c0d5a4f522669a5afecdc0eec3a6337ba16b3d190fea79d"
    ),
    "docs/sidekiq/sidekiq-inspection.md": (
        "8d24047e3efbe487b3366fa7815ce288cfe1d5c3292fd01864e8ffa7b7359a42"
    ),
    "docs/sidekiq/sidekiq-concurrency-limit.md": (
        "49a2dea3ff401b8e6f6ac9f2236d42a08ae3519d27d2402812a12695ba056dec"
    ),
    "docs/uncategorized/upgrade-and-rollback.md": (
        "9fdae356a2d44f6735955f366f760d47186f1786abce1fbb3fe62a38bdf8c89c"
    ),
}


def synthetic_case_bundle() -> HandoffCaseBundle:
    facts = [
        KnowledgeFact(
            fact_id="queue-scale-rule",
            title="Queue recovery threshold",
            text="When queue depth exceeds 10, scale the ledger worker pool to three workers.",
            source="operations-runbook.md#queue-recovery",
            in_actual_corpus=True,
            normal_retrieval_surfaces=True,
        ),
        KnowledgeFact(
            fact_id="migration-reversible-command",
            title="Migration rollback guard",
            text="Before rolling back migration M47, run ledgerctl migration mark-reversible M47.",
            source="deployment-runbook-complete.md#migration-m47",
            in_actual_corpus=False,
            normal_retrieval_surfaces=True,
        ),
        KnowledgeFact(
            fact_id="phoenix-replay-rule",
            title="Phoenix settlement replay",
            text="A stalled settlement batch is internally called Phoenix; replay it with batch mode safe.",
            source="incident-history.md#phoenix",
            in_actual_corpus=True,
            normal_retrieval_surfaces=False,
        ),
        KnowledgeFact(
            fact_id="signing-key-rotation-rule",
            title="Signing-key rotation",
            text="Rotate the report signing key through the isolated vault rotation tool.",
            source="security-runbook.md#report-signing",
            in_actual_corpus=True,
            normal_retrieval_surfaces=True,
        ),
    ]
    tasks = [
        TaskDefinition(
            task_id="task-control-queue",
            title="Recover a growing ledger queue",
            objective="Return the degraded ledger queue to a healthy operating state.",
            business_impact="Settlement updates remain delayed while the queue is degraded.",
            success_criteria=["Worker count is three", "Queue state is healthy"],
            required_fact_ids=["queue-scale-rule"],
            required_tool_ids=["scale_workers"],
            available_tool_ids=["inspect_queue", "scale_workers"],
            reference_actions=["inspect_queue", "scale_workers:3"],
            verifier_id="queue_health_verifier",
            expected_failure_cause=FailureCause.SUPPORTED_CONTROL,
        ),
        TaskDefinition(
            task_id="task-corpus-gap-rollback",
            title="Roll back migration M47",
            objective="Restore ledger-api version 2.3.1 after a failed migration deployment.",
            business_impact="The service cannot safely recover without the project-specific guard step.",
            success_criteria=["M47 is marked reversible", "Version 2.3.1 is active"],
            required_fact_ids=["migration-reversible-command"],
            required_tool_ids=["mark_migration_reversible", "rollback_release"],
            available_tool_ids=["mark_migration_reversible", "rollback_release"],
            reference_actions=["mark_migration_reversible:M47", "rollback_release:2.3.1"],
            verifier_id="rollback_verifier",
            expected_failure_cause=FailureCause.CORPUS_GAP,
        ),
        TaskDefinition(
            task_id="task-retrieval-gap-phoenix",
            title="Recover a stalled settlement batch",
            objective="Replay settlement batch B-204 without duplicating completed entries.",
            business_impact="A stalled settlement batch delays customer ledger updates.",
            success_criteria=["Batch B-204 is replayed in safe mode", "No duplicate entries"],
            required_fact_ids=["phoenix-replay-rule"],
            required_tool_ids=["replay_batch"],
            available_tool_ids=["inspect_batch", "replay_batch"],
            reference_actions=["inspect_batch:B-204", "replay_batch:B-204:safe"],
            verifier_id="batch_replay_verifier",
            expected_failure_cause=FailureCause.RETRIEVAL_GAP,
        ),
        TaskDefinition(
            task_id="task-agent-gap-key-rotation",
            title="Rotate the report signing key",
            objective="Replace the expiring report signing key without exposing key material.",
            business_impact="New reports cannot be signed after the current key expires.",
            success_criteria=["A new signing key is active", "Old key material is not exposed"],
            required_fact_ids=["signing-key-rotation-rule"],
            required_tool_ids=["vault_rotate_signing_key"],
            available_tool_ids=["inspect_key_status"],
            reference_actions=["inspect_key_status", "vault_rotate_signing_key"],
            verifier_id="signing_key_verifier",
            expected_failure_cause=FailureCause.AGENT_TOOL_GAP,
        ),
    ]
    actual_facts = [fact.fact_id for fact in facts if fact.in_actual_corpus]
    complete_facts = [fact.fact_id for fact in facts]
    case = HandoffCase(
        case_id=SYNTHETIC_CASE_ID,
        title="Ledger service maintainer handover",
        role="Senior platform engineer",
        owner="Synthetic Engineering Team",
        description=(
            "A safe, fictional handover used to validate HandoffProof records, "
            "failure controls and deterministic task oracles."
        ),
        created_at=datetime.now(UTC),
        current_corpus_version_id="actual-v1",
        corpus_versions=[
            CorpusVersion(
                version_id="actual-v1",
                label="Approved handover",
                description="The realistic handover corpus presented to the successor.",
                fact_ids=actual_facts,
            ),
            CorpusVersion(
                version_id="complete-oracle-v1",
                label="Gold-complete corpus",
                description="Test-only evidence used to isolate corpus-caused failures.",
                fact_ids=complete_facts,
            ),
        ],
        task_ids=[task.task_id for task in tasks],
        phase="agent_execution_ready",
    )
    return HandoffCaseBundle(case=case, facts=facts, tasks=tasks)


def gitlab_runbooks_case_bundle(corpus_root: Path) -> HandoffCaseBundle:
    """Build a source-derived benchmark after verifying its pinned local corpus."""
    manifest_path = corpus_root / "corpus-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"GitLab corpus manifest not found: {manifest_path}")
    # Windows PowerShell 5.1 may emit a UTF-8 BOM. Accept it defensively even
    # though the bundled fetch script now writes BOM-free UTF-8.
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("repository") != GITLAB_REPOSITORY:
        raise ValueError("GitLab corpus repository does not match the approved source.")
    if manifest.get("commit") != GITLAB_COMMIT:
        raise ValueError("GitLab corpus commit does not match the pinned benchmark commit.")
    if manifest.get("license") != "MIT":
        raise ValueError("GitLab corpus license metadata is not the expected MIT license.")
    entries = {item["path"]: item for item in manifest.get("files", [])}
    for relative_path, expected_hash in GITLAB_SOURCE_HASHES.items():
        entry = entries.get(relative_path)
        if entry is None or entry.get("sha256") != expected_hash:
            raise ValueError(f"Manifest hash mismatch for {relative_path}.")
        source_path = corpus_root / Path(relative_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Pinned GitLab source missing: {source_path}")
        actual_hash = sha256(source_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Source integrity check failed for {relative_path}.")

    review = BenchmarkStatus.SOURCE_DERIVED_REVIEW_PENDING
    facts = [
        KnowledgeFact(
            fact_id="gitlab-queue-diagnostic-checks",
            title="Unprocessed Sidekiq queue diagnostic checks",
            text=(
                "Before intervention, determine whether metrics are reported for the "
                "affected queue and whether its jobs are scheduled in both Chef and "
                "Kubernetes configuration."
            ),
            source="sidekiq-queue-not-being-processed.md#resolution",
            in_actual_corpus=True,
            normal_retrieval_surfaces=True,
            source_path="docs/sidekiq/sidekiq-queue-not-being-processed.md",
            source_sha256=GITLAB_SOURCE_HASHES["docs/sidekiq/sidekiq-queue-not-being-processed.md"],
            source_commit=GITLAB_COMMIT,
            review_status=review,
        ),
        KnowledgeFact(
            fact_id="gitlab-rollback-preconditions",
            title="GitLab.com application rollback preconditions",
            text=(
                "Before rollback, require an S1/S2 issue or outage document, page IMOC "
                "and DBRE, obtain DBRE database-impact review or IMOC sign-off if DBRE "
                "cannot review, then work with Delivery to initiate rollback via ChatOps."
            ),
            source="upgrade-and-rollback.md#application-rollback",
            in_actual_corpus=False,
            normal_retrieval_surfaces=True,
            source_path="docs/uncategorized/upgrade-and-rollback.md",
            source_sha256=GITLAB_SOURCE_HASHES["docs/uncategorized/upgrade-and-rollback.md"],
            source_commit=GITLAB_COMMIT,
            review_status=review,
        ),
        KnowledgeFact(
            fact_id="gitlab-sidekiq-runtime-inspection",
            title="Non-destructive Sidekiq runtime inspection",
            text=(
                "Connect with gitlab-rails console, instantiate Sidekiq::Workers, and "
                "inspect process ID, worker class, and runtime to identify the longest "
                "running job; the worker view is instantaneous."
            ),
            source="sidekiq-inspection.md#find-just-the-longest-running-job",
            in_actual_corpus=True,
            normal_retrieval_surfaces=False,
            source_path="docs/sidekiq/sidekiq-inspection.md",
            source_sha256=GITLAB_SOURCE_HASHES["docs/sidekiq/sidekiq-inspection.md"],
            source_commit=GITLAB_COMMIT,
            review_status=review,
        ),
        KnowledgeFact(
            fact_id="gitlab-concurrency-backlog-response",
            title="Concurrency-limit backlog response",
            text=(
                "For a concurrency-limit backlog above 100,000 jobs for over one hour, "
                "compare arrival and resume rates. If arrival remains higher and the "
                "worker can safely handle it, a temporary feature flag may disable the "
                "limit; monitor draining, restore the flag, and create a root-cause issue."
            ),
            source="sidekiq-concurrency-limit.md#sidekiqconcurrencylimitqueuebacklogged-alert",
            in_actual_corpus=True,
            normal_retrieval_surfaces=True,
            source_path="docs/sidekiq/sidekiq-concurrency-limit.md",
            source_sha256=GITLAB_SOURCE_HASHES["docs/sidekiq/sidekiq-concurrency-limit.md"],
            source_commit=GITLAB_COMMIT,
            review_status=review,
        ),
    ]
    tasks = [
        TaskDefinition(
            task_id="gitlab-control-queue-evidence",
            title="Investigate an unprocessed Sidekiq queue",
            objective=(
                "Collect the documented evidence needed before proposing intervention "
                "for the simulated mailers queue."
            ),
            business_impact="Queued mail jobs are accumulating and delivery is delayed.",
            success_criteria=[
                "Queue metrics were checked",
                "Chef scheduling was checked",
                "Kubernetes scheduling was checked",
            ],
            required_fact_ids=["gitlab-queue-diagnostic-checks"],
            required_tool_ids=["inspect_sidekiq_metrics", "inspect_sidekiq_scheduling"],
            available_tool_ids=["inspect_sidekiq_metrics", "inspect_sidekiq_scheduling"],
            reference_actions=[
                "inspect_sidekiq_metrics:mailers",
                "inspect_sidekiq_scheduling:mailers",
            ],
            verifier_id="gitlab_queue_evidence_verifier",
            expected_failure_cause=FailureCause.SUPPORTED_CONTROL,
        ),
        TaskDefinition(
            task_id="gitlab-corpus-gap-rollback",
            title="Authorize a simulated GitLab.com rollback",
            objective=(
                "Complete every documented coordination and database-review gate before "
                "requesting a simulated rollback for incident INC-4242."
            ),
            business_impact="An unsafe rollback could worsen a simulated production incident.",
            success_criteria=[
                "IMOC was paged",
                "DBRE was paged",
                "Database impact was reviewed",
                "Delivery rollback was requested",
            ],
            required_fact_ids=["gitlab-rollback-preconditions"],
            required_tool_ids=[
                "page_gitlab_imoc",
                "page_gitlab_dbre",
                "record_gitlab_db_review",
                "request_gitlab_delivery_rollback",
            ],
            available_tool_ids=[
                "page_gitlab_imoc",
                "page_gitlab_dbre",
                "record_gitlab_db_review",
                "request_gitlab_delivery_rollback",
            ],
            reference_actions=[
                "page_gitlab_imoc:INC-4242",
                "page_gitlab_dbre:INC-4242",
                "record_gitlab_db_review:approved",
                "request_gitlab_delivery_rollback:INC-4242",
            ],
            verifier_id="gitlab_rollback_gate_verifier",
            expected_failure_cause=FailureCause.CORPUS_GAP,
        ),
        TaskDefinition(
            task_id="gitlab-retrieval-gap-runtime-inspection",
            title="Inspect the longest-running Sidekiq job",
            objective=(
                "Use only the simulated read-only console to identify the longest-running "
                "job and record its process, class, and runtime."
            ),
            business_impact="A stuck worker cannot be assessed safely without runtime evidence.",
            success_criteria=[
                "Read-only console connected",
                "Longest-running job evidence recorded",
            ],
            required_fact_ids=["gitlab-sidekiq-runtime-inspection"],
            required_tool_ids=["connect_sidekiq_console", "inspect_longest_sidekiq_job"],
            available_tool_ids=[
                "connect_sidekiq_console",
                "inspect_longest_sidekiq_job",
            ],
            reference_actions=[
                "connect_sidekiq_console",
                "inspect_longest_sidekiq_job",
            ],
            verifier_id="gitlab_runtime_inspection_verifier",
            expected_failure_cause=FailureCause.RETRIEVAL_GAP,
        ),
        TaskDefinition(
            task_id="gitlab-agent-gap-concurrency",
            title="Relieve a simulated concurrency-limit backlog",
            objective=(
                "Apply the documented guarded response for a sustained backlog without "
                "touching any real GitLab system."
            ),
            business_impact="A sustained backlog risks simulated Redis memory saturation.",
            success_criteria=[
                "Arrival and resume rates were compared",
                "Temporary limit disablement was applied",
                "Queue drain was verified",
                "Limit was restored",
                "Root-cause issue was recorded",
            ],
            required_fact_ids=["gitlab-concurrency-backlog-response"],
            required_tool_ids=[
                "inspect_concurrency_rates",
                "set_sidekiq_concurrency_limit",
                "monitor_concurrency_queue",
                "record_concurrency_root_cause",
            ],
            available_tool_ids=[
                "inspect_concurrency_rates",
                "monitor_concurrency_queue",
                "record_concurrency_root_cause",
            ],
            reference_actions=[
                "inspect_concurrency_rates",
                "set_sidekiq_concurrency_limit:disable",
                "monitor_concurrency_queue",
                "set_sidekiq_concurrency_limit:restore",
                "record_concurrency_root_cause",
            ],
            verifier_id="gitlab_concurrency_response_verifier",
            expected_failure_cause=FailureCause.AGENT_TOOL_GAP,
        ),
    ]
    actual_fact_ids = [fact.fact_id for fact in facts if fact.in_actual_corpus]
    case = HandoffCase(
        case_id=GITLAB_CASE_ID,
        title="GitLab runbooks handover benchmark",
        role="Simulated GitLab.com on-call successor",
        owner="HandoffProof benchmark maintainers",
        description=(
            "A source-derived benchmark using pinned public GitLab runbooks with "
            "simulated state, bounded tools, and deterministic verifiers."
        ),
        created_at=datetime.now(UTC),
        current_corpus_version_id="gitlab-actual-v1",
        corpus_versions=[
            CorpusVersion(
                version_id="gitlab-actual-v1",
                label="Mutated public-runbook handover",
                description=(
                    "Pinned source-derived facts with one intentional omission and one "
                    "seeded retrieval miss."
                ),
                fact_ids=actual_fact_ids,
            ),
            CorpusVersion(
                version_id="gitlab-complete-oracle-v1",
                label="Gold-complete public-runbook facts",
                description="Test-only complete fact set derived from the pinned corpus.",
                fact_ids=[fact.fact_id for fact in facts],
            ),
        ],
        task_ids=[task.task_id for task in tasks],
        phase="source_benchmark_review_pending",
        benchmark_status=review,
        provenance=SourceProvenance(
            repository=GITLAB_REPOSITORY,
            commit=GITLAB_COMMIT,
            license="MIT",
            manifest_path=str(manifest_path),
            verified_file_count=len(GITLAB_SOURCE_HASHES),
            integrity_verified=True,
        ),
        limitations=[
            "Task states, tool responses, and verifiers are simulated locally.",
            "Answer keys are source-derived but await independent human review.",
            "No GitLab production systems, credentials, or internal acceptance process are used.",
        ],
    )
    return HandoffCaseBundle(case=case, facts=facts, tasks=tasks)
