import shutil
from pathlib import Path
from typing import ClassVar

from typer.testing import CliRunner

from srag.cli import app
from srag.handoffproof.domain import (
    AgentDecision,
    AgentResponse,
    AgentTurn,
    BenchmarkStatus,
    CorpusMode,
    DecisionSource,
    DecisionType,
    FailureCause,
    HandoffCaseBundle,
    KnowledgeFact,
    RetrievalMode,
    ReviewChecklist,
    ReviewDecision,
    TaskDefinition,
    ToolSpec,
)
from srag.handoffproof.execution import AgentExperimentRunner
from srag.handoffproof.sandbox import SyntheticTaskEnvironment
from srag.handoffproof.scenarios import (
    GITLAB_CASE_ID,
    GITLAB_COMMIT,
    GITLAB_CORPUS_DIRNAME,
    SYNTHETIC_CASE_ID,
    gitlab_runbooks_case_bundle,
    synthetic_case_bundle,
)
from srag.handoffproof.service import HandoffProofService
from srag.handoffproof.storage import HandoffStore


class ControlledRetriever:
    def retrieve(
        self,
        bundle: HandoffCaseBundle,
        task: TaskDefinition,
        corpus_mode: CorpusMode,
        retrieval_mode: RetrievalMode,
    ) -> list[KnowledgeFact]:
        current_version = next(
            version
            for version in bundle.case.corpus_versions
            if version.version_id == bundle.case.current_corpus_version_id
        )
        current_fact_ids = set(current_version.fact_ids)
        facts = [
            fact
            for fact in bundle.facts
            if corpus_mode is CorpusMode.COMPLETE or fact.fact_id in current_fact_ids
        ]
        if retrieval_mode is RetrievalMode.NORMAL:
            facts = [fact for fact in facts if fact.normal_retrieval_surfaces]
        return [fact for fact in facts if fact.fact_id in task.required_fact_ids]


class ControlledSuccessorAgent:
    model = "controlled-test-agent"
    arguments: ClassVar[dict[str, dict[str, str | int | bool]]] = {
        "scale_workers": {"count": 3},
        "mark_migration_reversible": {"migration_id": "M47"},
        "rollback_release": {"version": "2.3.1"},
        "replay_batch": {"batch_id": "B-204", "mode": "safe"},
        "vault_rotate_signing_key": {},
        "inspect_sidekiq_metrics": {"queue": "mailers"},
        "inspect_sidekiq_scheduling": {"queue": "mailers"},
        "page_gitlab_imoc": {"incident": "INC-4242"},
        "page_gitlab_dbre": {"incident": "INC-4242"},
        "record_gitlab_db_review": {"approved": True},
        "request_gitlab_delivery_rollback": {"incident": "INC-4242"},
        "connect_sidekiq_console": {},
        "inspect_longest_sidekiq_job": {},
    }

    def decide(
        self,
        task: TaskDefinition,
        evidence: list[KnowledgeFact],
        tools: list[ToolSpec],
        state: dict[str, str | int | bool | None],
        prior_turns: list[AgentTurn],
    ) -> AgentResponse:
        evidence_ids = [fact.fact_id for fact in evidence]
        tool_ids = {tool.tool_id for tool in tools}
        if not set(task.required_fact_ids).issubset(evidence_ids):
            return self._stop("Required handover evidence is missing.")
        if not set(task.required_tool_ids).issubset(tool_ids):
            return self._stop("A required bounded tool is unavailable.")
        if task.task_id == "task-control-queue":
            tool_id = "scale_workers"
        elif task.task_id == "task-corpus-gap-rollback":
            tool_id = (
                "mark_migration_reversible"
                if state["migration_reversible"] is False
                else "rollback_release"
            )
        elif task.task_id == "task-retrieval-gap-phoenix":
            tool_id = "replay_batch"
        elif task.task_id == "gitlab-control-queue-evidence":
            tool_id = (
                "inspect_sidekiq_metrics"
                if state["metrics_checked"] is False
                else "inspect_sidekiq_scheduling"
            )
        elif task.task_id == "gitlab-corpus-gap-rollback":
            if state["imoc_paged"] is False:
                tool_id = "page_gitlab_imoc"
            elif state["dbre_paged"] is False:
                tool_id = "page_gitlab_dbre"
            elif state["database_reviewed"] is False:
                tool_id = "record_gitlab_db_review"
            else:
                tool_id = "request_gitlab_delivery_rollback"
        elif task.task_id == "gitlab-retrieval-gap-runtime-inspection":
            tool_id = (
                "connect_sidekiq_console"
                if state["console_connected"] is False
                else "inspect_longest_sidekiq_job"
            )
        else:
            tool_id = "vault_rotate_signing_key"
        return AgentResponse(
            decision=AgentDecision(
                decision=DecisionType.ACT,
                reason="Apply the cited handover rule through the bounded tool.",
                evidence_fact_ids=evidence_ids,
                tool_id=tool_id,
                arguments=self.arguments[tool_id],
            )
        )

    @staticmethod
    def _stop(reason: str) -> AgentResponse:
        return AgentResponse(
            decision=AgentDecision(
                decision=DecisionType.STOP_BLOCKED,
                reason=reason,
                blocked_reason=reason,
            )
        )


def test_synthetic_case_persists_complete_phase_two_records(tmp_path: Path) -> None:
    service = HandoffProofService(tmp_path)

    created = service.initialize_synthetic_case()
    loaded = service.get_case(SYNTHETIC_CASE_ID)

    assert created.case.case_id == SYNTHETIC_CASE_ID
    assert loaded.case.current_corpus_version_id == "actual-v1"
    assert len(loaded.case.corpus_versions) == 2
    assert len(loaded.facts) == 4
    assert len(loaded.tasks) == 4
    assert service.list_cases()[0].task_count == 4


def test_fixture_rehearsal_classifies_all_four_seeded_patterns(tmp_path: Path) -> None:
    service = HandoffProofService(tmp_path)
    service.initialize_synthetic_case()

    result = service.rehearse_case(SYNTHETIC_CASE_ID)

    assert result.mode == "deterministic_fixture_rehearsal"
    assert result.all_patterns_match is True
    assert {task.observed_failure_cause for task in result.tasks} == set(FailureCause)
    assert all(len(task.cells) == 4 for task in result.tasks)


def test_fixture_rehearsal_keeps_agent_gap_when_oracle_evidence_is_available(
    tmp_path: Path,
) -> None:
    service = HandoffProofService(tmp_path)
    service.initialize_synthetic_case()

    result = service.rehearse_case(
        SYNTHETIC_CASE_ID,
        "task-agent-gap-key-rotation",
    )

    task = result.tasks[0]
    assert task.observed_failure_cause is FailureCause.AGENT_TOOL_GAP
    assert all(not cell.passed for cell in task.cells)
    assert all(cell.unavailable_tool_ids == ["vault_rotate_signing_key"] for cell in task.cells)


def test_gitlab_benchmark_verifies_pinned_sources_and_persists_review_gate(
    tmp_path: Path,
) -> None:
    reference_root = Path(__file__).parents[1] / "data" / "reference-corpora"
    service = HandoffProofService(tmp_path, reference_corpora_root=reference_root)

    bundle = service.initialize_gitlab_benchmark(reset=True)

    assert bundle.case.case_id == GITLAB_CASE_ID
    assert bundle.case.benchmark_status is BenchmarkStatus.SOURCE_DERIVED_REVIEW_PENDING
    assert bundle.case.provenance is not None
    assert bundle.case.provenance.commit == GITLAB_COMMIT
    assert bundle.case.provenance.integrity_verified is True
    assert bundle.case.provenance.verified_file_count == 4
    assert len(bundle.facts) == 4
    assert len(bundle.tasks) == 4
    assert all(fact.source_sha256 and fact.source_commit for fact in bundle.facts)


def test_gitlab_source_benchmark_rehearsal_classifies_all_four_controls(
    tmp_path: Path,
) -> None:
    reference_root = Path(__file__).parents[1] / "data" / "reference-corpora"
    service = HandoffProofService(tmp_path, reference_corpora_root=reference_root)
    service.initialize_gitlab_benchmark(reset=True)

    result = service.rehearse_case(GITLAB_CASE_ID)

    assert result.mode == "source_derived_benchmark_rehearsal"
    assert result.all_patterns_match is True
    assert {task.observed_failure_cause for task in result.tasks} == set(FailureCause)
    assert "simulations" in result.limitation


def test_gitlab_benchmark_rejects_tampered_pinned_source(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "data" / "reference-corpora" / GITLAB_CORPUS_DIRNAME
    copied = tmp_path / GITLAB_CORPUS_DIRNAME
    shutil.copytree(source, copied)
    target = copied / "docs" / "sidekiq" / "sidekiq-inspection.md"
    target.write_text(target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")

    try:
        gitlab_runbooks_case_bundle(copied)
    except ValueError as error:
        assert "integrity check failed" in str(error)
    else:
        raise AssertionError("A modified pinned source must be rejected")


def test_gitlab_benchmark_accepts_utf8_bom_manifest(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "data" / "reference-corpora" / GITLAB_CORPUS_DIRNAME
    copied = tmp_path / GITLAB_CORPUS_DIRNAME
    shutil.copytree(source, copied)
    manifest = copied / "corpus-manifest.json"
    manifest.write_bytes(b"\xef\xbb\xbf" + manifest.read_bytes())

    bundle = gitlab_runbooks_case_bundle(copied)

    assert bundle.case.provenance is not None
    assert bundle.case.provenance.integrity_verified is True


def test_gitlab_simulator_requires_source_fact_for_rollback_action() -> None:
    corpus = Path(__file__).parents[1] / "data" / "reference-corpora" / GITLAB_CORPUS_DIRNAME
    task = next(
        task
        for task in gitlab_runbooks_case_bundle(corpus).tasks
        if task.task_id == "gitlab-corpus-gap-rollback"
    )
    environment = SyntheticTaskEnvironment(task)

    rejected = environment.execute("page_gitlab_imoc", {"incident": "INC-4242"}, [])
    accepted = environment.execute(
        "page_gitlab_imoc",
        {"incident": "INC-4242"},
        ["gitlab-rollback-preconditions"],
    )

    assert rejected.accepted is False
    assert accepted.accepted is True
    assert environment.snapshot()["imoc_paged"] is True


def test_gitlab_read_only_procedure_does_not_leak_through_tool_names() -> None:
    corpus = Path(__file__).parents[1] / "data" / "reference-corpora" / GITLAB_CORPUS_DIRNAME
    task = next(
        task
        for task in gitlab_runbooks_case_bundle(corpus).tasks
        if task.task_id == "gitlab-retrieval-gap-runtime-inspection"
    )
    environment = SyntheticTaskEnvironment(task)

    rejected = environment.execute("connect_sidekiq_console", {}, [])
    accepted = environment.execute(
        "connect_sidekiq_console",
        {},
        ["gitlab-sidekiq-runtime-inspection"],
    )

    assert rejected.accepted is False
    assert "missing: gitlab-sidekiq-runtime-inspection" in rejected.message
    assert accepted.accepted is True


def test_gitlab_benchmark_report_uses_latest_live_experiment_per_task(
    tmp_path: Path,
) -> None:
    reference_root = Path(__file__).parents[1] / "data" / "reference-corpora"
    store = HandoffStore(tmp_path)
    runner = AgentExperimentRunner(
        agent=ControlledSuccessorAgent(),
        retriever=ControlledRetriever(),
        store=store,
    )
    service = HandoffProofService(
        tmp_path,
        runner=runner,
        reference_corpora_root=reference_root,
    )
    bundle = service.initialize_gitlab_benchmark(reset=True)
    for task in bundle.tasks:
        experiment = runner.run_task(bundle, task)
        assert experiment.expected_pattern_matches is True

    report = service.create_benchmark_report(GITLAB_CASE_ID)

    assert report.matched_tasks == 4
    assert report.total_tasks == 4
    assert report.pattern_accuracy == 1.0
    assert report.source_integrity_verified is True
    assert report.human_review_complete is False
    assert report.claim_level == "source_derived_mechanism_evidence_only"
    assert service.get_case(GITLAB_CASE_ID).case.phase == "source_benchmark_evidence_ready"


def test_handoff_cli_is_available_without_removing_baseline_commands(tmp_path: Path) -> None:
    runner = CliRunner()
    environment = {"S_RAG_HANDOFF_DIR": str(tmp_path / "handoff")}

    created = runner.invoke(app, ["handoff", "init-demo"], env=environment)
    status = runner.invoke(app, ["handoff", "status"], env=environment)
    rehearsal = runner.invoke(app, ["handoff", "rehearse"], env=environment)
    root_help = runner.invoke(app, ["--help"], env=environment)

    assert created.exit_code == 0
    assert "synthetic-ledger-service-handover" in created.stdout
    assert status.exit_code == 0
    assert "HandoffProof cases" in status.stdout
    assert rehearsal.exit_code == 0
    assert "All patterns" not in rehearsal.stdout  # Rich output uses the compact summary.
    assert "matched" in rehearsal.stdout
    assert "ingest" in root_help.stdout
    assert "handoff" in root_help.stdout


def test_synthetic_mutation_requires_the_exact_retrieved_fact() -> None:
    task = next(
        task for task in synthetic_case_bundle().tasks if task.task_id == "task-control-queue"
    )
    environment = SyntheticTaskEnvironment(task)

    rejected = environment.execute("scale_workers", {"count": 3}, [])
    accepted = environment.execute("scale_workers", {"count": 3}, ["queue-scale-rule"])

    assert rejected.accepted is False
    assert "Evidence gate rejected" in rejected.message
    assert accepted.accepted is True
    assert environment.verify()[0] is True


def test_agent_runner_executes_and_persists_all_four_control_cells(tmp_path: Path) -> None:
    store = HandoffStore(tmp_path)
    service = HandoffProofService(tmp_path)
    bundle = service.initialize_synthetic_case(reset=True)
    runner = AgentExperimentRunner(
        agent=ControlledSuccessorAgent(),
        retriever=ControlledRetriever(),
        store=store,
    )

    for task in bundle.tasks:
        experiment = runner.run_task(bundle, task)
        assert experiment.expected_pattern_matches is True
        assert experiment.observed_failure_cause is task.expected_failure_cause
        assert len(experiment.runs) == 4

    runs = store.list_runs(SYNTHETIC_CASE_ID)
    assert len(runs) == 16
    assert {run.status.value for run in runs} == {"passed", "blocked"}


def test_preflight_blocks_impossible_cells_without_calling_the_model(tmp_path: Path) -> None:
    store = HandoffStore(tmp_path)
    service = HandoffProofService(tmp_path)
    bundle = service.initialize_synthetic_case(reset=True)
    task = next(task for task in bundle.tasks if task.task_id == "task-corpus-gap-rollback")
    runner = AgentExperimentRunner(
        agent=ControlledSuccessorAgent(),
        retriever=ControlledRetriever(),
        store=store,
    )

    experiment = runner.run_task(bundle, task)

    actual_runs = [run for run in experiment.runs if run.corpus_mode is CorpusMode.ACTUAL]
    complete_runs = [run for run in experiment.runs if run.corpus_mode is CorpusMode.COMPLETE]
    assert all(run.preflight_blocked for run in actual_runs)
    assert all(run.status.value == "blocked" for run in actual_runs)
    assert all(len(run.turns) == 1 for run in actual_runs)
    assert all(
        run.turns[0].decision_source is DecisionSource.ORCHESTRATOR_PREFLIGHT for run in actual_runs
    )
    assert all(not run.preflight_blocked for run in complete_runs)
    assert all(
        turn.decision_source is DecisionSource.MODEL for run in complete_runs for turn in run.turns
    )


def test_independent_review_requires_all_checks_and_all_tasks(tmp_path: Path) -> None:
    reference_root = Path(__file__).parents[1] / "data" / "reference-corpora"
    service = HandoffProofService(tmp_path, reference_corpora_root=reference_root)
    service.initialize_gitlab_benchmark(reset=True)
    packet = service.create_review_packet(GITLAB_CASE_ID)

    assert packet.complete is False
    assert len(service.list_reviews(GITLAB_CASE_ID)) == 4
    first_review = service.list_reviews(GITLAB_CASE_ID)[0]
    try:
        service.submit_benchmark_review(
            first_review.review_id,
            "Independent Reviewer",
            ReviewDecision.APPROVED,
            "Checked source and simulator.",
            ReviewChecklist(source_alignment=True),
        )
    except ValueError as error:
        assert "every independent-review check" in str(error)
    else:
        raise AssertionError("Partial review checklists must not approve a task")

    complete_checklist = ReviewChecklist(
        source_alignment=True,
        start_state_realism=True,
        reference_actions_complete=True,
        verifier_criteria_valid=True,
    )
    for review in service.list_reviews(GITLAB_CASE_ID):
        packet = service.submit_benchmark_review(
            review.review_id,
            "Independent Reviewer",
            ReviewDecision.APPROVED,
            "Validated against pinned source and bounded simulator.",
            complete_checklist,
        )

    assert packet.complete is True
    assert packet.approved_count == 4
    reviewed_case = service.get_case(GITLAB_CASE_ID).case
    assert reviewed_case.benchmark_status is BenchmarkStatus.HUMAN_REVIEWED
    assert reviewed_case.phase == "human_reviewed_benchmark"


def test_only_isolated_corpus_gap_can_create_expert_question(tmp_path: Path) -> None:
    store = HandoffStore(tmp_path)
    runner = AgentExperimentRunner(
        agent=ControlledSuccessorAgent(),
        retriever=ControlledRetriever(),
        store=store,
    )
    service = HandoffProofService(tmp_path, runner=runner)
    bundle = service.initialize_synthetic_case(reset=True)
    retrieval_task = next(
        task for task in bundle.tasks if task.task_id == "task-retrieval-gap-phoenix"
    )
    experiment = runner.run_task(bundle, retrieval_task)

    try:
        service.create_expert_questions(experiment.experiment_id)
    except ValueError as error:
        assert "only for an isolated corpus gap" in str(error)
    else:
        raise AssertionError("Retrieval gaps must not create expert questions")


def test_approved_answer_versions_corpus_and_replay_proves_repair(tmp_path: Path) -> None:
    store = HandoffStore(tmp_path)
    runner = AgentExperimentRunner(
        agent=ControlledSuccessorAgent(),
        retriever=ControlledRetriever(),
        store=store,
    )
    service = HandoffProofService(tmp_path, runner=runner)
    bundle = service.initialize_synthetic_case(reset=True)
    task = next(task for task in bundle.tasks if task.task_id == "task-corpus-gap-rollback")
    source = runner.run_task(bundle, task)

    questions = service.create_expert_questions(source.experiment_id)
    assert len(questions) == 1
    answer = service.submit_expert_answer(
        questions[0].question_id,
        "Before rollback, run ledgerctl migration mark-reversible M47.",
        "expert://platform-lead/migration-m47",
        "Platform Lead",
    )
    before_approval = service.get_case(bundle.case.case_id)
    assert before_approval.case.current_corpus_version_id == "actual-v1"

    patch = service.approve_expert_answer(answer.answer_id, "Handover Owner")
    after_approval = service.get_case(bundle.case.case_id)
    assert patch.previous_version_id == "actual-v1"
    assert patch.new_version_id == after_approval.case.current_corpus_version_id
    assert "migration-reversible-command" in after_approval.case.corpus_versions[-1].fact_ids

    replay = service.replay_patch(patch.patch_id)
    assert replay.before_status.value == "blocked"
    assert replay.after_status.value == "passed"
    assert replay.before_passed is False
    assert replay.after_passed is True
    assert replay.repaired is True
    assert service.get_case(bundle.case.case_id).case.phase == "repair_validated"
