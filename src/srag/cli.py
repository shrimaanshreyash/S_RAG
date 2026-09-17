from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from ollama import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from srag.config import Settings
from srag.domain import Chunk, SearchHit
from srag.handoffproof.domain import (
    CaseRehearsal,
    FailureCause,
    ReviewChecklist,
    ReviewDecision,
)
from srag.handoffproof.factory import create_handoff_service
from srag.handoffproof.scenarios import SYNTHETIC_CASE_ID
from srag.handoffproof.service import HandoffProofService
from srag.service import RagService
from srag.typesafe_evidence import POLICY_VERSION, TypeSafeEvidenceJudge

app = typer.Typer(
    name="srag",
    help="Small local RAG with visible parsing, retrieval, context and citations.",
    no_args_is_help=True,
)
console = Console()
handoff_app = typer.Typer(
    help="Run HandoffProof fixtures and evidence-gated local successor-agent experiments.",
    no_args_is_help=True,
)
app.add_typer(handoff_app, name="handoff")
typesafe_app = typer.Typer(
    help="Inspect and test the optional TypeSafe evidence governor.",
    no_args_is_help=True,
)
app.add_typer(typesafe_app, name="typesafe")


def _service() -> RagService:
    return RagService(Settings())


def _handoff_service() -> HandoffProofService:
    return create_handoff_service(Settings())


def _duration(value: float) -> str:
    return f"{value * 1000:.1f} ms" if value < 1 else f"{value:.2f} s"


def _cause_label(cause: FailureCause) -> str:
    return cause.value.replace("_", " ").title()


def _typesafe_judge(settings: Settings) -> TypeSafeEvidenceJudge:
    secret = settings.typesafe_api_key
    return TypeSafeEvidenceJudge(
        api_key=secret.get_secret_value() if secret is not None else "",
        model=settings.typesafe_model,
        timeout_seconds=settings.typesafe_timeout_seconds,
        max_workers=settings.typesafe_max_workers,
    )


@typesafe_app.command("status")
def typesafe_status() -> None:
    """Show local TypeSafe configuration without making an API call."""
    settings = Settings()
    secret = settings.typesafe_api_key
    key_configured = secret is not None and bool(secret.get_secret_value().strip())
    console.print(
        Panel.fit(
            f"Enabled for RAG: {'yes' if settings.typesafe_enabled else 'no'}\n"
            f"API key configured: {'yes' if key_configured else 'no'}\n"
            f"Model: {settings.typesafe_model}\n"
            f"Candidate passages: {settings.typesafe_candidate_top_k}\n"
            f"Concurrent calls: {settings.typesafe_max_workers}\n"
            f"Policy: {POLICY_VERSION}",
            title="TypeSafe evidence governor",
        )
    )


@typesafe_app.command("probe")
def typesafe_probe() -> None:
    """Make one small live call using public, non-sensitive sample text."""
    settings = Settings()
    sample = SearchHit(
        rank=1,
        score=1.0,
        chunk=Chunk(
            chunk_id="typesafe-probe:c1",
            document_id="typesafe-probe",
            filename="public-sample.md",
            text=(
                "Before changing a stalled job queue, record the queue depth and the "
                "longest-running job so the intervention has diagnostic evidence."
            ),
            section="Queue inspection",
            block_ids=["probe-b1"],
            token_estimate=28,
        ),
    )
    try:
        judgment = _typesafe_judge(settings).judge(
            "What evidence should an engineer collect before changing a stalled job queue?",
            [sample],
        )[0]
    except Exception as error:
        console.print(f"[bold red]TypeSafe probe failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    table = Table(title="Live Jev evidence judgment")
    table.add_column("Signal")
    table.add_column("Probability", justify="right")
    table.add_row("Relevant", f"{judgment.is_relevant:.3f}")
    table.add_row("Usable answer evidence", f"{judgment.contains_answer_evidence:.3f}")
    table.add_row("Contradicts query premise", f"{judgment.contradicts_query_premise:.3f}")
    table.add_row("Prompt injection", f"{judgment.contains_prompt_injection:.3f}")
    console.print(table)
    console.print(
        Panel.fit(
            f"Route: {judgment.route.value}\n"
            f"Model: {judgment.model}\n"
            f"Latency: {_duration(judgment.latency_seconds)}\n"
            f"Tokens: {judgment.input_tokens} input, {judgment.output_tokens} output\n"
            f"Policy: {judgment.policy_version}",
            title="Probe result",
        )
    )


def _print_rehearsal(rehearsal: CaseRehearsal) -> None:
    console.print(
        Panel.fit(
            f"[bold]Case:[/bold] {rehearsal.case_id}\n"
            f"[bold]Mode:[/bold] {rehearsal.mode}\n"
            f"[bold]Fixture patterns:[/bold] "
            f"{'matched' if rehearsal.all_patterns_match else 'mismatch'}\n"
            f"[dim]{rehearsal.limitation}[/dim]",
            title="HandoffProof rehearsal",
        )
    )
    for task in rehearsal.tasks:
        table = Table(title=task.title, show_lines=True)
        table.add_column("Corpus")
        table.add_column("Retrieval")
        table.add_column("Result")
        table.add_column("Verifier")
        for cell in task.cells:
            table.add_row(
                cell.corpus_mode.value,
                cell.retrieval_mode.value,
                "PASS" if cell.passed else "BLOCKED",
                cell.verifier_message,
            )
        console.print(table)
        console.print(
            f"Expected: [bold]{_cause_label(task.expected_failure_cause)}[/bold] | "
            f"Observed: [bold]{_cause_label(task.observed_failure_cause)}[/bold] | "
            f"{'match' if task.expected_pattern_matches else 'mismatch'}"
        )


@handoff_app.command("init-demo")
def handoff_init_demo(
    reset: Annotated[
        bool,
        typer.Option("--reset", help="Replace the existing synthetic case fixture."),
    ] = False,
) -> None:
    """Create the safe four-task synthetic handover case."""
    bundle = _handoff_service().initialize_synthetic_case(reset=reset)
    console.print(
        Panel.fit(
            f"[bold green]Ready[/bold green] {bundle.case.title}\n"
            f"Case ID: {bundle.case.case_id}\n"
            f"Role: {bundle.case.role}\n"
            f"Tasks: {len(bundle.tasks)}\n"
            f"Phase: {bundle.case.phase}",
            title="HandoffProof synthetic case",
        )
    )


@handoff_app.command("init-gitlab")
def handoff_init_gitlab(
    reset: Annotated[
        bool,
        typer.Option("--reset", help="Rebuild the pinned GitLab source benchmark."),
    ] = False,
) -> None:
    """Verify the pinned runbooks and create the source-derived benchmark."""
    try:
        bundle = _handoff_service().initialize_gitlab_benchmark(reset=reset)
    except (FileNotFoundError, ValueError) as error:
        console.print(f"[bold red]GitLab benchmark refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    provenance = bundle.case.provenance
    console.print(
        Panel.fit(
            f"[bold green]Integrity verified[/bold green] {bundle.case.title}\n"
            f"Case ID: {bundle.case.case_id}\n"
            f"Commit: {provenance.commit if provenance else 'unknown'}\n"
            f"Files verified: {provenance.verified_file_count if provenance else 0}\n"
            f"Tasks: {len(bundle.tasks)}\n"
            f"Review status: {bundle.case.benchmark_status.value}\n"
            "[dim]Operational state, tools, and verifiers remain local simulations.[/dim]",
            title="HandoffProof GitLab benchmark",
        )
    )


@handoff_app.command("status")
def handoff_status() -> None:
    """List persisted HandoffProof cases and their current phase."""
    cases = _handoff_service().list_cases()
    if not cases:
        console.print("No HandoffProof cases. Run: uv run srag handoff init-demo")
        return
    table = Table(title="HandoffProof cases")
    table.add_column("Case ID")
    table.add_column("Title")
    table.add_column("Role")
    table.add_column("Tasks", justify="right")
    table.add_column("Phase")
    for case in cases:
        table.add_row(
            case.case_id,
            case.title,
            case.role,
            str(case.task_count),
            case.phase,
        )
    console.print(table)


@handoff_app.command("show")
def handoff_show(
    case_id: Annotated[str, typer.Argument()] = SYNTHETIC_CASE_ID,
) -> None:
    """Show the corpus versions, facts and tasks in one handover case."""
    try:
        bundle = _handoff_service().get_case(case_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Case not found:[/bold red] {case_id}")
        raise typer.Exit(code=1) from error
    console.print(
        Panel.fit(
            f"{bundle.case.title}\nRole: {bundle.case.role}\nOwner: {bundle.case.owner}\n"
            f"Current corpus: {bundle.case.current_corpus_version_id}\n"
            f"Phase: {bundle.case.phase}\n"
            f"Benchmark status: {bundle.case.benchmark_status.value}\n"
            f"Pinned commit: "
            f"{bundle.case.provenance.commit if bundle.case.provenance else 'not applicable'}",
            title=bundle.case.case_id,
        )
    )
    table = Table(title="Representative tasks", show_lines=True)
    table.add_column("Task ID")
    table.add_column("Task")
    table.add_column("Expected fixture cause")
    table.add_column("Verifier")
    for task in bundle.tasks:
        table.add_row(
            task.task_id,
            task.title,
            _cause_label(task.expected_failure_cause),
            task.verifier_id,
        )
    console.print(table)


@handoff_app.command("rehearse")
def handoff_rehearse(
    case_id: Annotated[str, typer.Argument()] = SYNTHETIC_CASE_ID,
    task_id: Annotated[
        str | None,
        typer.Option("--task", help="Run one fixture task instead of the complete case."),
    ] = None,
) -> None:
    """Run the deterministic four-cell fixture rehearsal (not an AI-agent run)."""
    try:
        rehearsal = _handoff_service().rehearse_case(case_id, task_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Case not found:[/bold red] {case_id}")
        raise typer.Exit(code=1) from error
    except KeyError as error:
        console.print(f"[bold red]Task not found:[/bold red] {task_id}")
        raise typer.Exit(code=1) from error
    _print_rehearsal(rehearsal)


@handoff_app.command("run")
def handoff_run(
    case_id: Annotated[str, typer.Argument()] = SYNTHETIC_CASE_ID,
    task_id: Annotated[
        str,
        typer.Option("--task", help="Representative task to run through all four cells."),
    ] = "task-control-queue",
) -> None:
    """Run one real Ollama successor-agent experiment across the four control cells."""
    console.print(
        f"Running [bold]{task_id}[/bold] across four cells with the local successor agent..."
    )
    try:
        experiment = _handoff_service().run_agent_task(case_id, task_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Case not found:[/bold red] {case_id}")
        raise typer.Exit(code=1) from error
    except KeyError as error:
        console.print(f"[bold red]Task not found:[/bold red] {task_id}")
        raise typer.Exit(code=1) from error
    except Exception as error:
        console.print(f"[bold red]Agent experiment failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    table = Table(title=experiment.task_title, show_lines=True)
    table.add_column("Corpus")
    table.add_column("Retrieval")
    table.add_column("Status")
    table.add_column("Steps", justify="right")
    table.add_column("Evidence")
    table.add_column("Verifier")
    for run in experiment.runs:
        table.add_row(
            run.corpus_mode.value,
            run.retrieval_mode.value,
            run.status.value.upper(),
            str(len(run.turns)),
            ", ".join(run.retrieved_fact_ids) or "none",
            run.verifier_message,
        )
    console.print(table)
    console.print(
        f"Expected: [bold]{_cause_label(experiment.expected_failure_cause)}[/bold] | "
        f"Observed: [bold]{_cause_label(experiment.observed_failure_cause)}[/bold] | "
        f"{'match' if experiment.expected_pattern_matches else 'mismatch'}"
    )
    console.print(f"Experiment ID: {experiment.experiment_id}")


@handoff_app.command("runs")
def handoff_runs(
    case_id: Annotated[
        str | None,
        typer.Option("--case", help="Show runs for one handover case."),
    ] = None,
) -> None:
    """List persisted successor-agent cell runs."""
    runs = _handoff_service().list_runs(case_id)
    if not runs:
        console.print("No successor-agent runs have been recorded.")
        return
    table = Table(title="Successor-agent runs")
    table.add_column("Run ID")
    table.add_column("Task")
    table.add_column("Corpus")
    table.add_column("Retrieval")
    table.add_column("Status")
    for run in runs:
        table.add_row(
            run.run_id,
            run.task_id,
            run.corpus_mode.value,
            run.retrieval_mode.value,
            run.status.value,
        )
    console.print(table)


@handoff_app.command("benchmark-report")
def handoff_benchmark_report(case_id: Annotated[str, typer.Argument()]) -> None:
    """Aggregate the latest live experiment for every source-benchmark task."""
    try:
        report = _handoff_service().create_benchmark_report(case_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Case not found:[/bold red] {case_id}")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[bold red]Report refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    table = Table(title="Latest live causal results", show_lines=True)
    table.add_column("Task")
    table.add_column("Expected")
    table.add_column("Observed")
    table.add_column("Match")
    for task in report.task_results:
        table.add_row(
            task.task_id,
            _cause_label(task.expected_failure_cause),
            _cause_label(task.observed_failure_cause),
            "YES" if task.pattern_matched else "NO",
        )
    console.print(table)
    reduction_line = (
        f"Reduction from prior report: {report.turn_reduction} steps, "
        f"{report.unsupported_action_reduction} rejected actions\n"
        if report.baseline_report_id is not None
        else ""
    )
    report_summary = (
        f"Pattern accuracy: {report.matched_tasks}/{report.total_tasks} "
        f"({report.pattern_accuracy:.0%})\n"
        f"Source integrity: "
        f"{'verified' if report.source_integrity_verified else 'unverified'}\n"
        f"Human review: {'complete' if report.human_review_complete else 'pending'}\n"
        f"Trace steps: {report.total_turns} ({report.model_turns} model, "
        f"{report.preflight_blocked_cells} preflight-blocked cells)\n"
        f"Rejected actions: {report.unsupported_action_count}\n"
        f"{reduction_line}"
        f"Claim level: {report.claim_level}\n"
        f"Report ID: {report.report_id}"
    )
    console.print(
        Panel.fit(
            report_summary,
            title="HandoffProof benchmark report",
        )
    )


@handoff_app.command("inspect-run")
def handoff_inspect_run(run_id: Annotated[str, typer.Argument()]) -> None:
    """Inspect evidence, decisions, tool results and verifier output for one run."""
    try:
        run = _handoff_service().get_run(run_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Run not found:[/bold red] {run_id}")
        raise typer.Exit(code=1) from error
    console.print(
        Panel.fit(
            f"Task: {run.task_id}\nCorpus: {run.corpus_mode.value}\n"
            f"Retrieval: {run.retrieval_mode.value}\nStatus: {run.status.value}\n"
            f"Evidence: {', '.join(run.retrieved_fact_ids) or 'none'}\n"
            f"Verifier: {run.verifier_message}",
            title=run.run_id,
        )
    )
    for turn in run.turns:
        tool_line = "no tool"
        if turn.tool_result is not None:
            tool_line = (
                f"{turn.tool_result.tool_id}: "
                f"{'accepted' if turn.tool_result.accepted else 'rejected'} — "
                f"{turn.tool_result.message}"
            )
        console.print(
            Panel(
                f"Source: {turn.decision_source.value}\n"
                f"Decision: {turn.decision.decision.value}\n"
                f"Reason: {turn.decision.reason}\n"
                f"Citations: {', '.join(turn.decision.evidence_fact_ids) or 'none'}\n"
                f"Tool: {tool_line}",
                title=f"Step {turn.step_number}",
            )
        )


@handoff_app.command("review-packet")
def handoff_review_packet(case_id: Annotated[str, typer.Argument()]) -> None:
    """Create or reuse the pending independent-review packet."""
    try:
        packet = _handoff_service().create_review_packet(case_id)
    except (FileNotFoundError, ValueError) as error:
        console.print(f"[bold red]Review packet refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(
        Panel.fit(
            f"Packet ID: {packet.packet_id}\n"
            f"Approved: {packet.approved_count}/{packet.total_tasks}\n"
            f"Complete: {'yes' if packet.complete else 'no'}",
            title="Independent benchmark review",
        )
    )


@handoff_app.command("reviews")
def handoff_reviews(
    case_id: Annotated[str | None, typer.Option("--case")] = None,
) -> None:
    """List benchmark task reviews and their evidence status."""
    reviews = _handoff_service().list_reviews(case_id)
    table = Table(title="Independent task reviews")
    table.add_column("Review ID")
    table.add_column("Task")
    table.add_column("Decision")
    table.add_column("Reviewer")
    for review in reviews:
        table.add_row(
            review.review_id,
            review.task_id,
            review.decision.value,
            review.reviewer or "—",
        )
    console.print(table)


@handoff_app.command("review-task")
def handoff_review_task(
    review_id: Annotated[str, typer.Argument()],
    reviewer: Annotated[str, typer.Option("--by")],
    decision: Annotated[ReviewDecision, typer.Option("--decision")],
    notes: Annotated[str, typer.Option("--notes")] = "",
    confirm_all: Annotated[
        bool,
        typer.Option(
            "--confirm-all",
            help="Confirm source, start state, reference actions and verifier criteria.",
        ),
    ] = False,
) -> None:
    """Record a named human decision for one benchmark task."""
    checklist = ReviewChecklist(
        source_alignment=confirm_all,
        start_state_realism=confirm_all,
        reference_actions_complete=confirm_all,
        verifier_criteria_valid=confirm_all,
    )
    try:
        packet = _handoff_service().submit_benchmark_review(
            review_id,
            reviewer,
            decision,
            notes,
            checklist,
        )
    except (FileNotFoundError, ValueError) as error:
        console.print(f"[bold red]Review refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(
        f"Review recorded. Packet {packet.packet_id}: "
        f"{packet.approved_count}/{packet.total_tasks} approved."
    )


@handoff_app.command("ask-expert")
def handoff_ask_expert(experiment_id: Annotated[str, typer.Argument()]) -> None:
    """Create precise expert questions from a proven corpus-gap experiment."""
    try:
        questions = _handoff_service().create_expert_questions(experiment_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Experiment not found:[/bold red] {experiment_id}")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[bold red]Question refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    for question in questions:
        console.print(
            Panel(
                f"{question.prompt}\n\nMissing fact: {question.missing_fact_id}\n"
                f"Status: {question.status.value}",
                title=question.question_id,
            )
        )


@handoff_app.command("questions")
def handoff_questions(
    case_id: Annotated[
        str | None,
        typer.Option("--case", help="Show questions for one handover case."),
    ] = None,
) -> None:
    """List expert questions and their approval status."""
    questions = _handoff_service().list_questions(case_id)
    if not questions:
        console.print("No expert questions have been recorded.")
        return
    table = Table(title="Expert questions")
    table.add_column("Question ID")
    table.add_column("Task")
    table.add_column("Missing fact")
    table.add_column("Status")
    table.add_column("Answer ID")
    for question in questions:
        table.add_row(
            question.question_id,
            question.task_id,
            question.missing_fact_id,
            question.status.value,
            question.answer_id or "—",
        )
    console.print(table)


@handoff_app.command("answer")
def handoff_answer(
    question_id: Annotated[str, typer.Argument()],
    answer_text: Annotated[str, typer.Option("--text", help="Exact expert procedure.")],
    source_reference: Annotated[
        str,
        typer.Option("--source", help="Auditable source for the expert answer."),
    ],
    expert_name: Annotated[str, typer.Option("--expert", help="Answering expert name.")],
) -> None:
    """Submit an expert answer without changing the approved corpus."""
    try:
        answer = _handoff_service().submit_expert_answer(
            question_id,
            answer_text,
            source_reference,
            expert_name,
        )
    except FileNotFoundError as error:
        console.print(f"[bold red]Question not found:[/bold red] {question_id}")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[bold red]Answer refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(
        Panel.fit(
            f"Answer ID: {answer.answer_id}\nStatus: {answer.status.value}\n"
            "The corpus is unchanged until a separate approval command.",
            title="Expert answer recorded",
        )
    )


@handoff_app.command("approve")
def handoff_approve(
    answer_id: Annotated[str, typer.Argument()],
    approved_by: Annotated[str, typer.Option("--by", help="Approving owner name.")],
) -> None:
    """Approve one answer and create an immutable corpus version."""
    try:
        patch = _handoff_service().approve_expert_answer(answer_id, approved_by)
    except FileNotFoundError as error:
        console.print(f"[bold red]Answer not found:[/bold red] {answer_id}")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[bold red]Approval refused:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(
        Panel.fit(
            f"Patch ID: {patch.patch_id}\nPrevious: {patch.previous_version_id}\n"
            f"Current: {patch.new_version_id}\nFacts added: "
            f"{', '.join(patch.added_fact_ids)}",
            title="Approved corpus repair",
        )
    )


@handoff_app.command("replay")
def handoff_replay(patch_id: Annotated[str, typer.Argument()]) -> None:
    """Replay the identical task and compare its actual/normal outcome."""
    console.print("Replaying the patched task through all four live-agent cells...")
    try:
        replay = _handoff_service().replay_patch(patch_id)
    except FileNotFoundError as error:
        console.print(f"[bold red]Patch or source experiment not found:[/bold red] {patch_id}")
        raise typer.Exit(code=1) from error
    except (KeyError, ValueError, RuntimeError) as error:
        console.print(f"[bold red]Replay failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(
        Panel.fit(
            f"Before actual/normal: {replay.before_status.value.upper()}\n"
            f"After actual/normal: {replay.after_status.value.upper()}\n"
            f"Repair proven: {'YES' if replay.repaired else 'NO'}\n"
            f"Replay ID: {replay.replay_id}",
            title="Before/after repair proof",
        )
    )


@app.command()
def ingest(path: Annotated[Path, typer.Argument(exists=True, readable=True)]) -> None:
    """Parse, chunk, embed and index a document or directory."""
    try:
        for result in _service().ingest_path(path):
            console.print(
                Panel.fit(
                    f"[bold green]Ingested[/bold green] {result.document.filename}\n"
                    f"Document ID: {result.document.document_id}\n"
                    f"Canonical blocks: {len(result.document.blocks)}\n"
                    f"Chunks indexed: {len(result.chunks)}\n"
                    f"Canonical JSON: {result.canonical_path}\n"
                    f"Debug Markdown: {result.markdown_path}"
                )
            )
            metrics = result.metrics
            table = Table(title="Ingestion performance")
            table.add_column("Metric")
            table.add_column("Value", justify="right")
            table.add_row("Document size", f"{metrics.document_size_mb:.2f} MB")
            table.add_row("Parse latency", _duration(metrics.parse_seconds))
            table.add_row("Chunk latency", _duration(metrics.chunk_seconds))
            table.add_row("Artifact write latency", _duration(metrics.artifact_write_seconds))
            table.add_row(
                "Embedding + index latency",
                _duration(metrics.embedding_and_index_seconds),
            )
            table.add_row("Total ingest latency", _duration(metrics.total_seconds))
            table.add_row("Canonical blocks", str(metrics.canonical_blocks))
            table.add_row("Chunks indexed", str(metrics.chunks_indexed))
            table.add_row("Characters embedded", str(metrics.characters_embedded))
            table.add_row("Embedding/index throughput", f"{metrics.chunks_per_second:.2f} chunks/s")
            console.print(table)
    except Exception as error:
        console.print(f"[bold red]Ingest failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error


@app.command()
def ask(
    question: Annotated[str, typer.Argument()],
    top_k: Annotated[int | None, typer.Option(min=1, max=20)] = None,
    show_context: Annotated[bool, typer.Option("--show-context/--hide-context")] = True,
) -> None:
    """Retrieve evidence and answer with local Qwen plus citations."""
    try:
        result = _service().ask(question, top_k)
    except Exception as error:
        console.print(f"[bold red]Ask failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    console.print(f"[bold]Normalized question:[/bold] {result.normalized_question}")
    table = Table(title="Retrieved evidence", show_lines=True)
    table.add_column("Rank", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Chunk ID")
    table.add_column("Source")
    table.add_column("Pages")
    table.add_column("Section")
    for hit in result.hits:
        table.add_row(
            str(hit.rank),
            f"{hit.score:.4f}",
            hit.chunk.chunk_id,
            hit.chunk.filename,
            ", ".join(map(str, hit.chunk.page_numbers)) or "unknown",
            hit.chunk.section or "unknown",
        )
    console.print(table)
    if result.evidence_judgments:
        judge_table = Table(title="TypeSafe evidence decisions", show_lines=True)
        judge_table.add_column("Chunk")
        judge_table.add_column("Route")
        judge_table.add_column("Relevant", justify="right")
        judge_table.add_column("Evidence", justify="right")
        judge_table.add_column("Conflict", justify="right")
        judge_table.add_column("Injection", justify="right")
        for item in result.evidence_judgments:
            judge_table.add_row(
                item.chunk_id,
                item.route.value,
                f"{item.is_relevant:.2f}",
                f"{item.contains_answer_evidence:.2f}",
                f"{item.contradicts_query_premise:.2f}",
                f"{item.contains_prompt_injection:.2f}",
            )
        console.print(judge_table)
    if show_context:
        console.print(Panel(result.context, title="Final context sent to model"))
    console.print(Panel(result.answer, title="Answer"))
    console.print("[bold]Citation map:[/bold]")
    for citation in result.citations:
        pages = ", ".join(map(str, citation.page_numbers)) or "unknown"
        console.print(
            f"[{citation.marker}] {citation.filename} | pages {pages} | "
            f"{citation.section or 'unknown'} | {citation.chunk_id}"
        )
    metrics = result.metrics
    performance = Table(title="Query performance")
    performance.add_column("Metric")
    performance.add_column("Value", justify="right")
    performance.add_row("End-to-end latency", _duration(metrics.end_to_end_seconds))
    performance.add_row("Retrieval latency", _duration(metrics.retrieval_seconds))
    performance.add_row("Query embedding wall time", _duration(metrics.query_embedding_seconds))
    performance.add_row("Similarity search", _duration(metrics.similarity_search_seconds))
    performance.add_row("Embedding model load", _duration(metrics.embedding_model_load_seconds))
    performance.add_row("Embedding evaluation", _duration(metrics.embedding_eval_seconds))
    performance.add_row("Embedding input tokens", str(metrics.embedding_input_tokens))
    performance.add_row("Embedding dimensions", str(metrics.embedding_dimensions))
    performance.add_row("Generation wall time", _duration(metrics.generation_wall_seconds))
    performance.add_row("Time to first token", _duration(metrics.time_to_first_token_seconds))
    performance.add_row("Ollama model load", _duration(metrics.model_load_seconds))
    performance.add_row("Prompt evaluation", _duration(metrics.prompt_eval_seconds))
    performance.add_row("Generation evaluation", _duration(metrics.generation_eval_seconds))
    performance.add_row("Prompt tokens", str(metrics.prompt_tokens))
    performance.add_row("Output tokens", str(metrics.output_tokens))
    performance.add_row("Generation throughput", f"{metrics.output_tokens_per_second:.2f} tokens/s")
    performance.add_row("Retrieved chunks", str(metrics.retrieved_chunks))
    performance.add_row("Context characters", str(metrics.context_characters))
    if result.evidence_judgments:
        performance.add_row("TypeSafe wall time", _duration(metrics.typesafe_wall_seconds))
        performance.add_row("TypeSafe input tokens", str(metrics.typesafe_input_tokens))
        performance.add_row("TypeSafe output tokens", str(metrics.typesafe_output_tokens))
        performance.add_row("TypeSafe candidates", str(metrics.typesafe_candidates))
        performance.add_row("TypeSafe included", str(metrics.typesafe_included))
        performance.add_row("TypeSafe conflicts", str(metrics.typesafe_conflicts))
        performance.add_row("TypeSafe review", str(metrics.typesafe_review))
        performance.add_row("TypeSafe excluded", str(metrics.typesafe_excluded))
    console.print(performance)


@app.command("inspect")
def inspect_document(document_id: str) -> None:
    """Inspect persisted canonical blocks and chunks for one document."""
    try:
        service = _service()
        document = service.artifacts.load_document(document_id)
        chunks = service.index.chunks_for_document(document_id)
    except Exception as error:
        console.print(f"[bold red]Inspect failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    console.print(
        Panel.fit(
            f"{document.filename}\nID: {document.document_id}\n"
            f"SHA-256: {document.sha256}\nParser: {document.parser_name} "
            f"{document.parser_version}\nBlocks: {len(document.blocks)} | Chunks: {len(chunks)}"
        )
    )
    for chunk in chunks:
        pages = ", ".join(map(str, chunk.page_numbers)) or "unknown"
        console.print(
            Panel(
                chunk.text,
                title=f"{chunk.chunk_id} | pages {pages} | {chunk.section or 'unknown'}",
            )
        )


@app.command()
def status() -> None:
    """Show local models, indexed documents and chunk count."""
    settings = Settings()
    service = _service()
    models = Client(host=settings.ollama_host).list().models
    names = {model.model for model in models}
    documents = service.artifacts.list_documents()
    console.print(f"Ollama: {settings.ollama_host}")
    console.print(
        f"Generation model: {settings.generation_model} "
        f"({'ready' if settings.generation_model in names else 'missing'})"
    )
    console.print(
        f"Embedding model: {settings.embedding_model} "
        f"({'ready' if settings.embedding_model in names else 'missing'})"
    )
    console.print(f"Indexed documents: {len(documents)}")
    console.print(f"Indexed chunks: {service.index.count()}")
    for document in documents:
        console.print(f"- {document.document_id} | {document.filename} | {document.title}")


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Local interface to bind to.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535)] = 8765,
) -> None:
    """Run the local browser workbench without replacing the CLI."""
    console.print(f"S/RAG workbench: http://{host}:{port}")
    uvicorn.run("srag.webapp:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
