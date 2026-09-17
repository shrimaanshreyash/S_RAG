from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from srag.handoffproof.domain import (
    AgentCellRun,
    AnswerStatus,
    BenchmarkReport,
    BenchmarkReviewPacket,
    BenchmarkStatus,
    BenchmarkTaskResult,
    BenchmarkTaskReview,
    CaseRehearsal,
    CaseSummary,
    CellResult,
    CorpusMode,
    CorpusPatch,
    CorpusVersion,
    ExpertAnswer,
    ExpertQuestion,
    FailureCause,
    HandoffCaseBundle,
    QuestionStatus,
    RepairReplay,
    RetrievalMode,
    ReviewChecklist,
    ReviewDecision,
    RunSummary,
    TaskAgentExperiment,
    TaskDefinition,
    TaskRehearsal,
)
from srag.handoffproof.scenarios import (
    GITLAB_CASE_ID,
    GITLAB_CORPUS_DIRNAME,
    SYNTHETIC_CASE_ID,
    gitlab_runbooks_case_bundle,
    synthetic_case_bundle,
)
from srag.handoffproof.storage import HandoffStore

if TYPE_CHECKING:
    from srag.handoffproof.execution import AgentExperimentRunner


class HandoffProofService:
    def __init__(
        self,
        root: Path,
        runner: AgentExperimentRunner | None = None,
        reference_corpora_root: Path = Path("data/reference-corpora"),
    ) -> None:
        self.store = HandoffStore(root)
        self.runner = runner
        self.reference_corpora_root = reference_corpora_root

    def initialize_synthetic_case(self, *, reset: bool = False) -> HandoffCaseBundle:
        if not reset:
            try:
                return self.store.load_case(SYNTHETIC_CASE_ID)
            except FileNotFoundError:
                pass
        bundle = synthetic_case_bundle()
        self.store.save_case(bundle)
        return bundle

    def initialize_gitlab_benchmark(self, *, reset: bool = False) -> HandoffCaseBundle:
        if not reset:
            try:
                return self.store.load_case(GITLAB_CASE_ID)
            except FileNotFoundError:
                pass
        bundle = gitlab_runbooks_case_bundle(self.reference_corpora_root / GITLAB_CORPUS_DIRNAME)
        self.store.save_case(bundle)
        return bundle

    def list_cases(self) -> list[CaseSummary]:
        return self.store.list_cases()

    def get_case(self, case_id: str) -> HandoffCaseBundle:
        return self.store.load_case(case_id)

    def run_agent_task(self, case_id: str, task_id: str) -> TaskAgentExperiment:
        if self.runner is None:
            raise RuntimeError("The live successor-agent runner is not configured.")
        bundle = self.get_case(case_id)
        task = next((item for item in bundle.tasks if item.task_id == task_id), None)
        if task is None:
            raise KeyError(task_id)
        return self.runner.run_task(bundle, task)

    def list_runs(self, case_id: str | None = None) -> list[RunSummary]:
        return self.store.list_runs(case_id)

    def get_run(self, run_id: str) -> AgentCellRun:
        return self.store.load_run(run_id)

    def create_benchmark_report(self, case_id: str) -> BenchmarkReport:
        bundle = self.get_case(case_id)
        if bundle.case.provenance is None:
            raise ValueError("Benchmark reports require a provenance-backed source case.")
        latest_by_task: dict[str, TaskAgentExperiment] = {}
        for experiment in self.store.list_experiments(case_id):
            latest_by_task.setdefault(experiment.task_id, experiment)
        missing_tasks = [
            task.task_id for task in bundle.tasks if task.task_id not in latest_by_task
        ]
        if missing_tasks:
            raise ValueError(
                "Run live experiments before reporting; missing: " + ", ".join(missing_tasks)
            )
        task_results = []
        for task in bundle.tasks:
            experiment = latest_by_task[task.task_id]
            task_results.append(
                BenchmarkTaskResult(
                    task_id=task.task_id,
                    experiment_id=experiment.experiment_id,
                    expected_failure_cause=experiment.expected_failure_cause,
                    observed_failure_cause=experiment.observed_failure_cause,
                    pattern_matched=experiment.expected_pattern_matches,
                    total_turns=sum(len(run.turns) for run in experiment.runs),
                    unsupported_action_count=sum(
                        run.unsupported_action_count for run in experiment.runs
                    ),
                    model_turns=sum(
                        sum(turn.decision_source.value == "model" for turn in run.turns)
                        for run in experiment.runs
                    ),
                    preflight_blocked_cells=sum(run.preflight_blocked for run in experiment.runs),
                )
            )
        matched_tasks = sum(item.pattern_matched for item in task_results)
        review_complete = bundle.case.benchmark_status is BenchmarkStatus.HUMAN_REVIEWED
        baseline = next(
            (
                item
                for item in self.store.list_benchmark_reports(case_id)
                if item.preflight_blocked_cells == 0 and item.unsupported_action_count > 0
            ),
            None,
        )
        total_turns = sum(item.total_turns for item in task_results)
        unsupported_actions = sum(item.unsupported_action_count for item in task_results)
        report = BenchmarkReport(
            report_id=uuid4().hex,
            case_id=case_id,
            generated_at=datetime.now(UTC),
            benchmark_status=bundle.case.benchmark_status,
            claim_level=(
                "human_reviewed_benchmark"
                if review_complete
                else "source_derived_mechanism_evidence_only"
            ),
            source_integrity_verified=bundle.case.provenance.integrity_verified,
            human_review_complete=review_complete,
            matched_tasks=matched_tasks,
            total_tasks=len(task_results),
            pattern_accuracy=matched_tasks / len(task_results),
            total_turns=total_turns,
            unsupported_action_count=unsupported_actions,
            model_turns=sum(item.model_turns for item in task_results),
            preflight_blocked_cells=sum(item.preflight_blocked_cells for item in task_results),
            baseline_report_id=baseline.report_id if baseline is not None else None,
            turn_reduction=(baseline.total_turns - total_turns if baseline is not None else None),
            unsupported_action_reduction=(
                baseline.unsupported_action_count - unsupported_actions
                if baseline is not None
                else None
            ),
            task_results=task_results,
        )
        self.store.save_benchmark_report(report)
        if review_complete:
            bundle.case.phase = "human_reviewed_benchmark"
        elif self.store.list_review_packets(case_id):
            bundle.case.phase = "independent_review_pending"
        else:
            bundle.case.phase = "source_benchmark_evidence_ready"
        self.store.save_case(bundle)
        return report

    def latest_benchmark_report(self, case_id: str) -> BenchmarkReport | None:
        return self.store.latest_benchmark_report(case_id)

    def create_review_packet(self, case_id: str) -> BenchmarkReviewPacket:
        bundle = self.get_case(case_id)
        if bundle.case.provenance is None:
            raise ValueError("Human review packets require a provenance-backed source case.")
        existing = self.store.list_review_packets(case_id)
        if existing and not existing[0].complete:
            bundle.case.phase = "independent_review_pending"
            self.store.save_case(bundle)
            return existing[0]
        packet_id = uuid4().hex
        reviews = [
            BenchmarkTaskReview(
                review_id=uuid4().hex,
                packet_id=packet_id,
                case_id=case_id,
                task_id=task.task_id,
                task_title=task.title,
                created_at=datetime.now(UTC),
            )
            for task in bundle.tasks
        ]
        packet = BenchmarkReviewPacket(
            packet_id=packet_id,
            case_id=case_id,
            created_at=datetime.now(UTC),
            review_ids=[review.review_id for review in reviews],
            total_tasks=len(reviews),
        )
        for review in reviews:
            self.store.save_review(review)
        self.store.save_review_packet(packet)
        bundle.case.phase = "independent_review_pending"
        self.store.save_case(bundle)
        return packet

    def list_reviews(self, case_id: str | None = None) -> list[BenchmarkTaskReview]:
        return self.store.list_reviews(case_id)

    def submit_benchmark_review(
        self,
        review_id: str,
        reviewer: str,
        decision: ReviewDecision,
        notes: str,
        checklist: ReviewChecklist,
    ) -> BenchmarkReviewPacket:
        if not reviewer.strip():
            raise ValueError("Reviewer name is required.")
        if decision is ReviewDecision.PENDING:
            raise ValueError("Choose approved or changes_requested.")
        if decision is ReviewDecision.APPROVED and not checklist.complete():
            raise ValueError("Approval requires every independent-review check.")
        review = self.store.load_review(review_id)
        review.reviewer = reviewer.strip()
        review.decision = decision
        review.notes = notes.strip() or None
        review.checklist = checklist
        review.reviewed_at = datetime.now(UTC)
        self.store.save_review(review)

        packet = self.store.load_review_packet(review.packet_id)
        packet_reviews = [self.store.load_review(item) for item in packet.review_ids]
        packet.approved_count = sum(
            item.decision is ReviewDecision.APPROVED and item.checklist.complete()
            for item in packet_reviews
        )
        packet.complete = packet.approved_count == packet.total_tasks
        self.store.save_review_packet(packet)
        bundle = self.get_case(review.case_id)
        if packet.complete:
            bundle.case.benchmark_status = BenchmarkStatus.HUMAN_REVIEWED
            bundle.case.phase = "human_reviewed_benchmark"
        else:
            bundle.case.benchmark_status = BenchmarkStatus.SOURCE_DERIVED_REVIEW_PENDING
            bundle.case.phase = "independent_review_pending"
        self.store.save_case(bundle)
        return packet

    def create_expert_questions(self, experiment_id: str) -> list[ExpertQuestion]:
        experiment = self.store.load_experiment(experiment_id)
        if experiment.observed_failure_cause is not FailureCause.CORPUS_GAP:
            raise ValueError("Expert questions are allowed only for an isolated corpus gap.")
        bundle = self.get_case(experiment.case_id)
        task = self._find_task(bundle, experiment.task_id)
        current_fact_ids = self._current_fact_ids(bundle)
        missing_fact_ids = sorted(set(task.required_fact_ids) - current_fact_ids)
        if not missing_fact_ids:
            raise ValueError("The current approved corpus no longer has this gap.")
        existing = {
            (question.source_experiment_id, question.missing_fact_id): question
            for question in self.store.list_questions(experiment.case_id)
        }
        facts = {fact.fact_id: fact for fact in bundle.facts}
        questions: list[ExpertQuestion] = []
        for fact_id in missing_fact_ids:
            previous = existing.get((experiment_id, fact_id))
            if previous is not None:
                questions.append(previous)
                continue
            fact = facts[fact_id]
            question = ExpertQuestion(
                question_id=uuid4().hex,
                case_id=experiment.case_id,
                task_id=task.task_id,
                source_experiment_id=experiment_id,
                missing_fact_id=fact_id,
                prompt=(
                    f"For the task '{task.title}', what exact approved procedure supplies "
                    f"the missing handover knowledge '{fact.title}'? Include the action, "
                    "required parameters, safety conditions, and a source reference."
                ),
                created_at=datetime.now(UTC),
            )
            self.store.save_question(question)
            questions.append(question)
        return questions

    def list_questions(self, case_id: str | None = None) -> list[ExpertQuestion]:
        return self.store.list_questions(case_id)

    def submit_expert_answer(
        self,
        question_id: str,
        answer_text: str,
        source_reference: str,
        expert_name: str,
    ) -> ExpertAnswer:
        question = self.store.load_question(question_id)
        if question.status is not QuestionStatus.OPEN:
            raise ValueError("This expert question already has an answer.")
        if not answer_text.strip() or not source_reference.strip() or not expert_name.strip():
            raise ValueError("Answer, source reference, and expert name are required.")
        answer = ExpertAnswer(
            answer_id=uuid4().hex,
            question_id=question_id,
            answer_text=answer_text.strip(),
            source_reference=source_reference.strip(),
            expert_name=expert_name.strip(),
            submitted_at=datetime.now(UTC),
        )
        question.status = QuestionStatus.ANSWERED
        question.answer_id = answer.answer_id
        self.store.save_answer(answer)
        self.store.save_question(question)
        return answer

    def approve_expert_answer(self, answer_id: str, approved_by: str) -> CorpusPatch:
        if not approved_by.strip():
            raise ValueError("Approver name is required.")
        answer = self.store.load_answer(answer_id)
        if answer.status is not AnswerStatus.PENDING:
            raise ValueError("This expert answer has already been approved.")
        question = self.store.load_question(answer.question_id)
        if question.status is not QuestionStatus.ANSWERED:
            raise ValueError("The expert question is not awaiting approval.")
        bundle = self.get_case(question.case_id)
        current_fact_ids = self._current_fact_ids(bundle)
        if question.missing_fact_id in current_fact_ids:
            raise ValueError("The missing fact is already present in the approved corpus.")
        fact = next(
            (item for item in bundle.facts if item.fact_id == question.missing_fact_id),
            None,
        )
        if fact is None:
            raise ValueError("The benchmark oracle does not define the missing fact.")
        patch_id = uuid4().hex
        previous_version_id = bundle.case.current_corpus_version_id
        new_version_id = f"actual-repair-{patch_id[:8]}"
        fact.text = answer.answer_text
        fact.source = answer.source_reference
        fact.in_actual_corpus = True
        fact.normal_retrieval_surfaces = True
        bundle.case.corpus_versions.append(
            CorpusVersion(
                version_id=new_version_id,
                label="Expert-approved repair",
                description=(
                    f"Adds {question.missing_fact_id} from approved answer {answer.answer_id}."
                ),
                fact_ids=sorted(current_fact_ids | {question.missing_fact_id}),
            )
        )
        bundle.case.current_corpus_version_id = new_version_id
        bundle.case.phase = "repair_replay_ready"
        approved_at = datetime.now(UTC)
        answer.status = AnswerStatus.APPROVED
        answer.approved_by = approved_by.strip()
        answer.approved_at = approved_at
        question.status = QuestionStatus.APPROVED
        patch = CorpusPatch(
            patch_id=patch_id,
            case_id=question.case_id,
            task_id=question.task_id,
            source_experiment_id=question.source_experiment_id,
            question_id=question.question_id,
            answer_id=answer.answer_id,
            previous_version_id=previous_version_id,
            new_version_id=new_version_id,
            added_fact_ids=[question.missing_fact_id],
            applied_at=approved_at,
            approved_by=approved_by.strip(),
        )
        self.store.save_answer(answer)
        self.store.save_question(question)
        self.store.save_patch(patch)
        self.store.save_case(bundle)
        return patch

    def replay_patch(self, patch_id: str) -> RepairReplay:
        patch = self.store.load_patch(patch_id)
        if self.runner is None:
            raise RuntimeError("The live successor-agent runner is not configured.")
        bundle = self.get_case(patch.case_id)
        if not set(patch.added_fact_ids).issubset(self._current_fact_ids(bundle)):
            raise ValueError("The approved patch is not present in the current corpus.")
        task = self._find_task(bundle, patch.task_id)
        source = self.store.load_experiment(patch.source_experiment_id)
        replay_experiment = self.runner.run_task(
            bundle,
            task,
            expected_failure_cause=FailureCause.SUPPORTED_CONTROL,
        )
        before = self._actual_normal_run(source)
        after = self._actual_normal_run(replay_experiment)
        replay = RepairReplay(
            replay_id=uuid4().hex,
            case_id=patch.case_id,
            task_id=patch.task_id,
            patch_id=patch.patch_id,
            source_experiment_id=source.experiment_id,
            replay_experiment_id=replay_experiment.experiment_id,
            before_run_id=before.run_id,
            after_run_id=after.run_id,
            before_status=before.status,
            after_status=after.status,
            before_passed=before.passed,
            after_passed=after.passed,
            repaired=not before.passed and after.passed,
            run_at=datetime.now(UTC),
        )
        self.store.save_replay(replay)
        if replay.repaired:
            bundle.case.phase = "repair_validated"
            self.store.save_case(bundle)
        return replay

    def rehearse_case(self, case_id: str, task_id: str | None = None) -> CaseRehearsal:
        bundle = self.get_case(case_id)
        tasks = bundle.tasks
        if task_id is not None:
            tasks = [task for task in tasks if task.task_id == task_id]
            if not tasks:
                raise KeyError(task_id)
        rehearsals = [self._rehearse_task(bundle, task) for task in tasks]
        is_source_benchmark = bundle.case.case_id == GITLAB_CASE_ID
        return CaseRehearsal(
            case_id=case_id,
            run_at=datetime.now(UTC),
            mode=(
                "source_derived_benchmark_rehearsal"
                if is_source_benchmark
                else "deterministic_fixture_rehearsal"
            ),
            limitation=(
                "Facts come from hash-verified public GitLab runbooks. Task state, tools, "
                "and verifiers are local simulations; answer keys await human review."
                if is_source_benchmark
                else CaseRehearsal.model_fields["limitation"].default
            ),
            all_patterns_match=all(item.expected_pattern_matches for item in rehearsals),
            tasks=rehearsals,
        )

    @staticmethod
    def _rehearse_task(
        bundle: HandoffCaseBundle,
        task: TaskDefinition,
    ) -> TaskRehearsal:
        fact_by_id = {fact.fact_id: fact for fact in bundle.facts}
        current_fact_ids = HandoffProofService._current_fact_ids(bundle)
        cells: list[CellResult] = []
        for corpus_mode in CorpusMode:
            for retrieval_mode in RetrievalMode:
                corpus_fact_ids = {
                    fact.fact_id
                    for fact in bundle.facts
                    if corpus_mode is CorpusMode.COMPLETE or fact.fact_id in current_fact_ids
                }
                if retrieval_mode is RetrievalMode.ORACLE:
                    available_fact_ids = corpus_fact_ids
                else:
                    available_fact_ids = {
                        fact_id
                        for fact_id in corpus_fact_ids
                        if fact_by_id[fact_id].normal_retrieval_surfaces
                    }
                missing_fact_ids = sorted(set(task.required_fact_ids) - available_fact_ids)
                unavailable_tool_ids = sorted(
                    set(task.required_tool_ids) - set(task.available_tool_ids)
                )
                passed = not missing_fact_ids and not unavailable_tool_ids
                if passed:
                    message = f"{task.verifier_id}: reference actions satisfy all criteria"
                else:
                    reasons: list[str] = []
                    if missing_fact_ids:
                        reasons.append(f"missing evidence: {', '.join(missing_fact_ids)}")
                    if unavailable_tool_ids:
                        reasons.append(f"unavailable tools: {', '.join(unavailable_tool_ids)}")
                    message = f"{task.verifier_id}: blocked by {'; '.join(reasons)}"
                cells.append(
                    CellResult(
                        corpus_mode=corpus_mode,
                        retrieval_mode=retrieval_mode,
                        passed=passed,
                        available_fact_ids=sorted(available_fact_ids),
                        missing_fact_ids=missing_fact_ids,
                        unavailable_tool_ids=unavailable_tool_ids,
                        verifier_message=message,
                    )
                )
        observed = HandoffProofService._classify(cells)
        return TaskRehearsal(
            task_id=task.task_id,
            title=task.title,
            expected_failure_cause=task.expected_failure_cause,
            observed_failure_cause=observed,
            expected_pattern_matches=observed is task.expected_failure_cause,
            cells=cells,
        )

    @staticmethod
    def _classify(cells: list[CellResult]) -> FailureCause:
        outcomes = {(cell.corpus_mode, cell.retrieval_mode): cell.passed for cell in cells}
        actual_normal = outcomes[(CorpusMode.ACTUAL, RetrievalMode.NORMAL)]
        actual_oracle = outcomes[(CorpusMode.ACTUAL, RetrievalMode.ORACLE)]
        complete_normal = outcomes[(CorpusMode.COMPLETE, RetrievalMode.NORMAL)]
        complete_oracle = outcomes[(CorpusMode.COMPLETE, RetrievalMode.ORACLE)]
        if actual_normal and actual_oracle and complete_normal and complete_oracle:
            return FailureCause.SUPPORTED_CONTROL
        if not complete_oracle:
            return FailureCause.AGENT_TOOL_GAP
        if not actual_normal and not actual_oracle and complete_normal:
            return FailureCause.CORPUS_GAP
        if not actual_normal and actual_oracle and not complete_normal and complete_oracle:
            return FailureCause.RETRIEVAL_GAP
        return FailureCause.AGENT_TOOL_GAP

    @staticmethod
    def _current_fact_ids(bundle: HandoffCaseBundle) -> set[str]:
        version = next(
            item
            for item in bundle.case.corpus_versions
            if item.version_id == bundle.case.current_corpus_version_id
        )
        return set(version.fact_ids)

    @staticmethod
    def _find_task(bundle: HandoffCaseBundle, task_id: str) -> TaskDefinition:
        task = next((item for item in bundle.tasks if item.task_id == task_id), None)
        if task is None:
            raise KeyError(task_id)
        return task

    @staticmethod
    def _actual_normal_run(experiment: TaskAgentExperiment) -> AgentCellRun:
        return next(
            run
            for run in experiment.runs
            if run.corpus_mode is CorpusMode.ACTUAL and run.retrieval_mode is RetrievalMode.NORMAL
        )
