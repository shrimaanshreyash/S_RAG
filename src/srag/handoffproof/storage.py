from __future__ import annotations

import tempfile
from pathlib import Path

from srag.handoffproof.domain import (
    AgentCellRun,
    BenchmarkReport,
    BenchmarkReviewPacket,
    BenchmarkTaskReview,
    CaseSummary,
    CorpusPatch,
    ExpertAnswer,
    ExpertQuestion,
    HandoffCaseBundle,
    RepairReplay,
    RunSummary,
    TaskAgentExperiment,
)


class HandoffStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save_case(self, bundle: HandoffCaseBundle) -> Path:
        path = self.root / "cases" / f"{bundle.case.case_id}.json"
        self._atomic_write(path, bundle.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_case(self, case_id: str) -> HandoffCaseBundle:
        path = self.root / "cases" / f"{case_id}.json"
        if not path.exists():
            raise FileNotFoundError(case_id)
        return HandoffCaseBundle.model_validate_json(path.read_bytes())

    def list_cases(self) -> list[CaseSummary]:
        cases: list[CaseSummary] = []
        for path in sorted((self.root / "cases").glob("*.json")):
            bundle = HandoffCaseBundle.model_validate_json(path.read_bytes())
            cases.append(
                CaseSummary(
                    case_id=bundle.case.case_id,
                    title=bundle.case.title,
                    role=bundle.case.role,
                    phase=bundle.case.phase,
                    task_count=len(bundle.tasks),
                    current_corpus_version_id=bundle.case.current_corpus_version_id,
                )
            )
        return cases

    def save_run(self, run: AgentCellRun) -> Path:
        path = self.root / "runs" / f"{run.run_id}.json"
        self._atomic_write(path, run.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_run(self, run_id: str) -> AgentCellRun:
        path = self.root / "runs" / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(run_id)
        return AgentCellRun.model_validate_json(path.read_bytes())

    def list_runs(self, case_id: str | None = None) -> list[RunSummary]:
        runs: list[RunSummary] = []
        for path in sorted((self.root / "runs").glob("*.json")):
            run = AgentCellRun.model_validate_json(path.read_bytes())
            if case_id is not None and run.case_id != case_id:
                continue
            runs.append(
                RunSummary(
                    run_id=run.run_id,
                    case_id=run.case_id,
                    task_id=run.task_id,
                    corpus_mode=run.corpus_mode,
                    retrieval_mode=run.retrieval_mode,
                    status=run.status,
                    passed=run.passed,
                    finished_at=run.finished_at,
                )
            )
        return sorted(runs, key=lambda item: item.finished_at, reverse=True)

    def save_experiment(self, experiment: TaskAgentExperiment) -> Path:
        path = self.root / "experiments" / f"{experiment.experiment_id}.json"
        self._atomic_write(path, experiment.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_experiment(self, experiment_id: str) -> TaskAgentExperiment:
        path = self.root / "experiments" / f"{experiment_id}.json"
        if not path.exists():
            raise FileNotFoundError(experiment_id)
        return TaskAgentExperiment.model_validate_json(path.read_bytes())

    def list_experiments(self, case_id: str | None = None) -> list[TaskAgentExperiment]:
        experiments = [
            TaskAgentExperiment.model_validate_json(path.read_bytes())
            for path in sorted((self.root / "experiments").glob("*.json"))
        ]
        if case_id is not None:
            experiments = [item for item in experiments if item.case_id == case_id]
        return sorted(experiments, key=lambda item: item.run_at, reverse=True)

    def save_question(self, question: ExpertQuestion) -> Path:
        path = self.root / "questions" / f"{question.question_id}.json"
        self._atomic_write(path, question.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_question(self, question_id: str) -> ExpertQuestion:
        path = self.root / "questions" / f"{question_id}.json"
        if not path.exists():
            raise FileNotFoundError(question_id)
        return ExpertQuestion.model_validate_json(path.read_bytes())

    def list_questions(self, case_id: str | None = None) -> list[ExpertQuestion]:
        questions = [
            ExpertQuestion.model_validate_json(path.read_bytes())
            for path in sorted((self.root / "questions").glob("*.json"))
        ]
        if case_id is not None:
            questions = [question for question in questions if question.case_id == case_id]
        return sorted(questions, key=lambda item: item.created_at, reverse=True)

    def save_answer(self, answer: ExpertAnswer) -> Path:
        path = self.root / "answers" / f"{answer.answer_id}.json"
        self._atomic_write(path, answer.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_answer(self, answer_id: str) -> ExpertAnswer:
        path = self.root / "answers" / f"{answer_id}.json"
        if not path.exists():
            raise FileNotFoundError(answer_id)
        return ExpertAnswer.model_validate_json(path.read_bytes())

    def save_patch(self, patch: CorpusPatch) -> Path:
        path = self.root / "patches" / f"{patch.patch_id}.json"
        self._atomic_write(path, patch.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_patch(self, patch_id: str) -> CorpusPatch:
        path = self.root / "patches" / f"{patch_id}.json"
        if not path.exists():
            raise FileNotFoundError(patch_id)
        return CorpusPatch.model_validate_json(path.read_bytes())

    def save_replay(self, replay: RepairReplay) -> Path:
        path = self.root / "replays" / f"{replay.replay_id}.json"
        self._atomic_write(path, replay.model_dump_json(indent=2).encode("utf-8"))
        return path

    def save_benchmark_report(self, report: BenchmarkReport) -> Path:
        path = self.root / "benchmark-reports" / f"{report.report_id}.json"
        self._atomic_write(path, report.model_dump_json(indent=2).encode("utf-8"))
        return path

    def latest_benchmark_report(self, case_id: str) -> BenchmarkReport | None:
        reports = self.list_benchmark_reports(case_id)
        return max(reports, key=lambda item: item.generated_at, default=None)

    def list_benchmark_reports(self, case_id: str | None = None) -> list[BenchmarkReport]:
        reports = [
            BenchmarkReport.model_validate_json(path.read_bytes())
            for path in sorted((self.root / "benchmark-reports").glob("*.json"))
        ]
        if case_id is not None:
            reports = [report for report in reports if report.case_id == case_id]
        return sorted(reports, key=lambda item: item.generated_at, reverse=True)

    def save_review(self, review: BenchmarkTaskReview) -> Path:
        path = self.root / "reviews" / f"{review.review_id}.json"
        self._atomic_write(path, review.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_review(self, review_id: str) -> BenchmarkTaskReview:
        path = self.root / "reviews" / f"{review_id}.json"
        if not path.exists():
            raise FileNotFoundError(review_id)
        return BenchmarkTaskReview.model_validate_json(path.read_bytes())

    def list_reviews(self, case_id: str | None = None) -> list[BenchmarkTaskReview]:
        reviews = [
            BenchmarkTaskReview.model_validate_json(path.read_bytes())
            for path in sorted((self.root / "reviews").glob("*.json"))
        ]
        if case_id is not None:
            reviews = [review for review in reviews if review.case_id == case_id]
        return sorted(reviews, key=lambda item: item.created_at, reverse=True)

    def save_review_packet(self, packet: BenchmarkReviewPacket) -> Path:
        path = self.root / "review-packets" / f"{packet.packet_id}.json"
        self._atomic_write(path, packet.model_dump_json(indent=2).encode("utf-8"))
        return path

    def load_review_packet(self, packet_id: str) -> BenchmarkReviewPacket:
        path = self.root / "review-packets" / f"{packet_id}.json"
        if not path.exists():
            raise FileNotFoundError(packet_id)
        return BenchmarkReviewPacket.model_validate_json(path.read_bytes())

    def list_review_packets(self, case_id: str | None = None) -> list[BenchmarkReviewPacket]:
        packets = [
            BenchmarkReviewPacket.model_validate_json(path.read_bytes())
            for path in sorted((self.root / "review-packets").glob("*.json"))
        ]
        if case_id is not None:
            packets = [packet for packet in packets if packet.case_id == case_id]
        return sorted(packets, key=lambda item: item.created_at, reverse=True)

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(path)
