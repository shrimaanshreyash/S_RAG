from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FailureCause(str, Enum):
    SUPPORTED_CONTROL = "supported_control"
    CORPUS_GAP = "corpus_gap"
    RETRIEVAL_GAP = "retrieval_gap"
    AGENT_TOOL_GAP = "agent_tool_gap"


class CorpusMode(str, Enum):
    ACTUAL = "actual"
    COMPLETE = "complete"


class RetrievalMode(str, Enum):
    NORMAL = "normal"
    ORACLE = "oracle"


class DecisionType(str, Enum):
    ACT = "act"
    STOP_SUCCESS = "stop_success"
    STOP_BLOCKED = "stop_blocked"


class DecisionSource(str, Enum):
    MODEL = "model"
    ORCHESTRATOR_PREFLIGHT = "orchestrator_preflight"


class RunStatus(str, Enum):
    PASSED = "passed"
    BLOCKED = "blocked"
    FAILED = "failed"
    ERROR = "error"


class QuestionStatus(str, Enum):
    OPEN = "open"
    ANSWERED = "answered"
    APPROVED = "approved"


class AnswerStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"


class BenchmarkStatus(str, Enum):
    SYNTHETIC_CONTROL = "synthetic_control"
    SOURCE_DERIVED_REVIEW_PENDING = "source_derived_review_pending"
    HUMAN_REVIEWED = "human_reviewed"


class ReviewDecision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class SourceProvenance(BaseModel):
    repository: str
    commit: str
    license: str
    manifest_path: str
    verified_file_count: int
    integrity_verified: bool


class KnowledgeFact(BaseModel):
    fact_id: str
    title: str
    text: str
    source: str
    in_actual_corpus: bool
    normal_retrieval_surfaces: bool
    source_path: str | None = None
    source_sha256: str | None = None
    source_commit: str | None = None
    review_status: BenchmarkStatus = BenchmarkStatus.SYNTHETIC_CONTROL


class CorpusVersion(BaseModel):
    version_id: str
    label: str
    description: str
    fact_ids: list[str] = Field(default_factory=list)
    approved: bool = True


class TaskDefinition(BaseModel):
    task_id: str
    title: str
    objective: str
    business_impact: str
    success_criteria: list[str]
    required_fact_ids: list[str]
    required_tool_ids: list[str]
    available_tool_ids: list[str]
    reference_actions: list[str]
    verifier_id: str
    expected_failure_cause: FailureCause


class HandoffCase(BaseModel):
    case_id: str
    title: str
    role: str
    owner: str
    description: str
    created_at: datetime
    current_corpus_version_id: str
    corpus_versions: list[CorpusVersion]
    task_ids: list[str]
    phase: str = "fixture_rehearsal"
    benchmark_status: BenchmarkStatus = BenchmarkStatus.SYNTHETIC_CONTROL
    provenance: SourceProvenance | None = None
    limitations: list[str] = Field(default_factory=list)


class HandoffCaseBundle(BaseModel):
    case: HandoffCase
    facts: list[KnowledgeFact]
    tasks: list[TaskDefinition]


class CaseSummary(BaseModel):
    case_id: str
    title: str
    role: str
    phase: str
    task_count: int
    current_corpus_version_id: str


class CellResult(BaseModel):
    corpus_mode: CorpusMode
    retrieval_mode: RetrievalMode
    passed: bool
    available_fact_ids: list[str]
    missing_fact_ids: list[str]
    unavailable_tool_ids: list[str]
    verifier_message: str


class TaskRehearsal(BaseModel):
    task_id: str
    title: str
    expected_failure_cause: FailureCause
    observed_failure_cause: FailureCause
    expected_pattern_matches: bool
    cells: list[CellResult]


class CaseRehearsal(BaseModel):
    case_id: str
    run_at: datetime
    mode: str = "deterministic_fixture_rehearsal"
    limitation: str = (
        "This validates seeded evidence, tool and verifier wiring. "
        "It is not a successor-agent result."
    )
    all_patterns_match: bool
    tasks: list[TaskRehearsal]


class ToolSpec(BaseModel):
    tool_id: str
    description: str
    arguments: dict[str, str] = Field(default_factory=dict)
    mutating: bool = False
    required_fact_ids: list[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    tool_id: str
    accepted: bool
    message: str
    observation: dict[str, str | int | bool | None] = Field(default_factory=dict)


class AgentDecision(BaseModel):
    decision: DecisionType
    reason: str
    evidence_fact_ids: list[str] = Field(default_factory=list)
    tool_id: str | None = None
    arguments: dict[str, str | int | bool] = Field(default_factory=dict)
    blocked_reason: str | None = None


class AgentResponse(BaseModel):
    decision: AgentDecision
    model_latency_seconds: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0


class AgentTurn(BaseModel):
    step_number: int
    decision: AgentDecision
    tool_result: ToolResult | None = None
    gate_message: str | None = None
    model_latency_seconds: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    decision_source: DecisionSource = DecisionSource.MODEL


class AgentCellRun(BaseModel):
    run_id: str
    case_id: str
    task_id: str
    corpus_mode: CorpusMode
    retrieval_mode: RetrievalMode
    model: str
    started_at: datetime
    finished_at: datetime
    status: RunStatus
    passed: bool
    retrieved_fact_ids: list[str]
    turns: list[AgentTurn]
    final_state: dict[str, str | int | bool | None]
    verifier_message: str
    unsupported_action_count: int = 0
    preflight_blocked: bool = False
    preflight_reason: str | None = None
    error: str | None = None


class TaskAgentExperiment(BaseModel):
    experiment_id: str
    case_id: str
    task_id: str
    task_title: str
    model: str
    run_at: datetime
    expected_failure_cause: FailureCause
    observed_failure_cause: FailureCause
    expected_pattern_matches: bool
    runs: list[AgentCellRun]


class RunSummary(BaseModel):
    run_id: str
    case_id: str
    task_id: str
    corpus_mode: CorpusMode
    retrieval_mode: RetrievalMode
    status: RunStatus
    passed: bool
    finished_at: datetime


class ExpertQuestion(BaseModel):
    question_id: str
    case_id: str
    task_id: str
    source_experiment_id: str
    missing_fact_id: str
    prompt: str
    created_at: datetime
    status: QuestionStatus = QuestionStatus.OPEN
    answer_id: str | None = None


class ExpertAnswer(BaseModel):
    answer_id: str
    question_id: str
    answer_text: str
    source_reference: str
    expert_name: str
    submitted_at: datetime
    status: AnswerStatus = AnswerStatus.PENDING
    approved_by: str | None = None
    approved_at: datetime | None = None


class CorpusPatch(BaseModel):
    patch_id: str
    case_id: str
    task_id: str
    source_experiment_id: str
    question_id: str
    answer_id: str
    previous_version_id: str
    new_version_id: str
    added_fact_ids: list[str]
    applied_at: datetime
    approved_by: str


class RepairReplay(BaseModel):
    replay_id: str
    case_id: str
    task_id: str
    patch_id: str
    source_experiment_id: str
    replay_experiment_id: str
    before_run_id: str
    after_run_id: str
    before_status: RunStatus
    after_status: RunStatus
    before_passed: bool
    after_passed: bool
    repaired: bool
    run_at: datetime


class BenchmarkTaskResult(BaseModel):
    task_id: str
    experiment_id: str
    expected_failure_cause: FailureCause
    observed_failure_cause: FailureCause
    pattern_matched: bool
    total_turns: int
    unsupported_action_count: int
    model_turns: int = 0
    preflight_blocked_cells: int = 0


class BenchmarkReport(BaseModel):
    report_id: str
    case_id: str
    generated_at: datetime
    benchmark_status: BenchmarkStatus
    claim_level: str
    source_integrity_verified: bool
    human_review_complete: bool
    matched_tasks: int
    total_tasks: int
    pattern_accuracy: float
    total_turns: int
    unsupported_action_count: int
    model_turns: int = 0
    preflight_blocked_cells: int = 0
    baseline_report_id: str | None = None
    turn_reduction: int | None = None
    unsupported_action_reduction: int | None = None
    task_results: list[BenchmarkTaskResult]


class ReviewChecklist(BaseModel):
    source_alignment: bool = False
    start_state_realism: bool = False
    reference_actions_complete: bool = False
    verifier_criteria_valid: bool = False

    def complete(self) -> bool:
        return all(self.model_dump().values())


class BenchmarkTaskReview(BaseModel):
    review_id: str
    packet_id: str
    case_id: str
    task_id: str
    task_title: str
    created_at: datetime
    decision: ReviewDecision = ReviewDecision.PENDING
    checklist: ReviewChecklist = Field(default_factory=ReviewChecklist)
    reviewer: str | None = None
    notes: str | None = None
    reviewed_at: datetime | None = None


class BenchmarkReviewPacket(BaseModel):
    packet_id: str
    case_id: str
    created_at: datetime
    review_ids: list[str]
    approved_count: int = 0
    total_tasks: int
    complete: bool = False
