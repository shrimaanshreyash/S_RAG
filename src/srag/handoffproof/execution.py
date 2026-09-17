from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from srag.handoffproof.agent import SuccessorAgent
from srag.handoffproof.domain import (
    AgentCellRun,
    AgentDecision,
    AgentTurn,
    CorpusMode,
    DecisionSource,
    DecisionType,
    FailureCause,
    HandoffCaseBundle,
    RetrievalMode,
    RunStatus,
    TaskAgentExperiment,
    TaskDefinition,
    ToolResult,
)
from srag.handoffproof.retrieval import EvidenceRetriever
from srag.handoffproof.sandbox import SyntheticTaskEnvironment
from srag.handoffproof.storage import HandoffStore


class AgentExperimentRunner:
    def __init__(
        self,
        agent: SuccessorAgent,
        retriever: EvidenceRetriever,
        store: HandoffStore,
        max_steps: int = 6,
    ) -> None:
        self.agent = agent
        self.retriever = retriever
        self.store = store
        self.max_steps = max_steps

    def run_task(
        self,
        bundle: HandoffCaseBundle,
        task: TaskDefinition,
        expected_failure_cause: FailureCause | None = None,
    ) -> TaskAgentExperiment:
        runs = [
            self._run_cell(bundle, task, corpus_mode, retrieval_mode)
            for corpus_mode in CorpusMode
            for retrieval_mode in RetrievalMode
        ]
        failed_cells = [run for run in runs if run.status is RunStatus.ERROR]
        if failed_cells:
            details = "; ".join(
                f"{run.corpus_mode.value}/{run.retrieval_mode.value}: {run.error}"
                for run in failed_cells
            )
            raise RuntimeError(f"One or more agent cells could not run: {details}")
        observed = self.classify_runs(runs)
        experiment = TaskAgentExperiment(
            experiment_id=uuid4().hex,
            case_id=bundle.case.case_id,
            task_id=task.task_id,
            task_title=task.title,
            model=self.agent.model,
            run_at=datetime.now(UTC),
            expected_failure_cause=expected_failure_cause or task.expected_failure_cause,
            observed_failure_cause=observed,
            expected_pattern_matches=observed
            is (expected_failure_cause or task.expected_failure_cause),
            runs=runs,
        )
        self.store.save_experiment(experiment)
        return experiment

    def _run_cell(
        self,
        bundle: HandoffCaseBundle,
        task: TaskDefinition,
        corpus_mode: CorpusMode,
        retrieval_mode: RetrievalMode,
    ) -> AgentCellRun:
        started_at = datetime.now(UTC)
        run_id = uuid4().hex
        environment = SyntheticTaskEnvironment(task)
        turns: list[AgentTurn] = []
        unsupported_actions = 0
        error_message: str | None = None
        stopped_blocked = False
        evidence = []
        preflight_blocked = False
        preflight_reason: str | None = None
        try:
            evidence = self.retriever.retrieve(
                bundle,
                task,
                corpus_mode,
                retrieval_mode,
            )
            available_fact_ids = {fact.fact_id for fact in evidence}
            available_tools = environment.available_tools()
            available_tool_ids = {tool.tool_id for tool in available_tools}
            missing_fact_ids = sorted(set(task.required_fact_ids) - available_fact_ids)
            missing_tool_ids = sorted(set(task.required_tool_ids) - available_tool_ids)
            if missing_fact_ids or missing_tool_ids:
                reasons: list[str] = []
                if missing_fact_ids:
                    reasons.append("missing evidence: " + ", ".join(missing_fact_ids))
                if missing_tool_ids:
                    reasons.append("unavailable tools: " + ", ".join(missing_tool_ids))
                preflight_reason = "; ".join(reasons)
                preflight_blocked = True
                stopped_blocked = True
                turns.append(
                    AgentTurn(
                        step_number=1,
                        decision=AgentDecision(
                            decision=DecisionType.STOP_BLOCKED,
                            reason="Feasibility preflight blocked the cell: " + preflight_reason,
                            blocked_reason=preflight_reason,
                        ),
                        gate_message=(
                            "The orchestrator did not call the model because the controlled "
                            "cell cannot satisfy the task prerequisites."
                        ),
                        decision_source=DecisionSource.ORCHESTRATOR_PREFLIGHT,
                    )
                )
            for step_number in range(1, self.max_steps + 1) if not preflight_blocked else []:
                response = self.agent.decide(
                    task,
                    evidence,
                    available_tools,
                    environment.snapshot(),
                    turns,
                )
                decision = response.decision
                gate_message: str | None = None
                tool_result: ToolResult | None = None
                if decision.decision is DecisionType.ACT:
                    tool_result, gate_message = self._execute_gated(
                        environment,
                        decision,
                        available_fact_ids,
                    )
                    if not tool_result.accepted:
                        unsupported_actions += 1
                elif decision.decision is DecisionType.STOP_BLOCKED:
                    stopped_blocked = True
                turn = AgentTurn(
                    step_number=step_number,
                    decision=decision,
                    tool_result=tool_result,
                    gate_message=gate_message,
                    model_latency_seconds=response.model_latency_seconds,
                    prompt_tokens=response.prompt_tokens,
                    output_tokens=response.output_tokens,
                )
                turns.append(turn)
                passed, _message = environment.verify()
                if passed or decision.decision in {
                    DecisionType.STOP_SUCCESS,
                    DecisionType.STOP_BLOCKED,
                }:
                    break
        except Exception as error:  # noqa: BLE001 - persist a complete failed run trace
            error_message = str(error)

        passed, verifier_message = environment.verify()
        if error_message is not None:
            status = RunStatus.ERROR
        elif passed:
            status = RunStatus.PASSED
        elif stopped_blocked:
            status = RunStatus.BLOCKED
        else:
            status = RunStatus.FAILED
        run = AgentCellRun(
            run_id=run_id,
            case_id=bundle.case.case_id,
            task_id=task.task_id,
            corpus_mode=corpus_mode,
            retrieval_mode=retrieval_mode,
            model=self.agent.model,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=status,
            passed=passed,
            retrieved_fact_ids=[fact.fact_id for fact in evidence],
            turns=turns,
            final_state=environment.snapshot(),
            verifier_message=verifier_message,
            unsupported_action_count=unsupported_actions,
            preflight_blocked=preflight_blocked,
            preflight_reason=preflight_reason,
            error=error_message,
        )
        self.store.save_run(run)
        return run

    @staticmethod
    def _execute_gated(
        environment: SyntheticTaskEnvironment,
        decision: AgentDecision,
        available_fact_ids: set[str],
    ) -> tuple[ToolResult, str | None]:
        if decision.tool_id is None:
            return (
                ToolResult(
                    tool_id="missing",
                    accepted=False,
                    message="Evidence gate rejected action without a tool ID.",
                    observation=environment.snapshot(),
                ),
                "Action decision did not name a tool.",
            )
        unknown_citations = sorted(set(decision.evidence_fact_ids) - available_fact_ids)
        if unknown_citations:
            return (
                ToolResult(
                    tool_id=decision.tool_id,
                    accepted=False,
                    message=(
                        "Evidence gate rejected citations not supplied to the agent: "
                        + ", ".join(unknown_citations)
                    ),
                    observation=environment.snapshot(),
                ),
                "Agent cited evidence outside the retrieved context.",
            )
        return (
            environment.execute(
                decision.tool_id,
                decision.arguments,
                decision.evidence_fact_ids,
            ),
            None,
        )

    @staticmethod
    def classify_runs(runs: list[AgentCellRun]) -> FailureCause:
        outcomes = {(run.corpus_mode, run.retrieval_mode): run.passed for run in runs}
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
