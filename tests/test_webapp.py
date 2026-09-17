from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from srag.config import Settings
from srag.domain import CanonicalDocument
from srag.handoffproof.service import HandoffProofService
from srag.webapp import create_app


class StubArtifacts:
    def __init__(self) -> None:
        self.document = CanonicalDocument(
            document_id="doc-1",
            filename="brief.txt",
            source_path=Path("brief.txt"),
            sha256="abc",
            size_bytes=12,
            title="Brief",
            parser_name="test",
            parser_version="1",
            parsed_at=datetime.now(UTC),
            blocks=[],
        )

    def list_documents(self) -> list[CanonicalDocument]:
        return [self.document]

    def load_document(self, document_id: str) -> CanonicalDocument:
        if document_id != "doc-1":
            raise FileNotFoundError(document_id)
        return self.document


class StubIndex:
    def count(self) -> int:
        return 0

    def chunks_for_document(self, document_id: str) -> list[Any]:
        return []


class StubService:
    def __init__(self, tmp_path: Path) -> None:
        self.settings = Settings(
            data_dir=tmp_path / "data",
            artifacts_dir=tmp_path / "artifacts",
            index_dir=tmp_path / "index",
            handoff_dir=tmp_path / "handoff",
        )
        self.artifacts = StubArtifacts()
        self.index = StubIndex()


def test_workbench_and_status_are_served(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    with TestClient(create_app(service)) as client:  # type: ignore[arg-type]
        page = client.get("/")
        status = client.get("/api/status")

    assert page.status_code == 200
    assert "Ask the indexed material" in page.text
    assert status.status_code == 200
    assert status.json()["documents"][0]["filename"] == "brief.txt"


def test_rejects_unsupported_upload(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    with TestClient(create_app(service)) as client:  # type: ignore[arg-type]
        response = client.post(
            "/api/documents",
            files=[("files", ("malware.exe", b"not really", "application/octet-stream"))],
        )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_handoffproof_fixture_is_available_through_web_api(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    with TestClient(create_app(service)) as client:  # type: ignore[arg-type]
        created = client.post("/api/handoff/synthetic")
        listed = client.get("/api/handoff/cases")
        rehearsed = client.post("/api/handoff/cases/synthetic-ledger-service-handover/rehearse")

    assert created.status_code == 200
    assert len(created.json()["tasks"]) == 4
    assert listed.status_code == 200
    assert listed.json()["cases"][0]["task_count"] == 4
    assert rehearsed.status_code == 200
    assert rehearsed.json()["all_patterns_match"] is True
    assert rehearsed.json()["mode"] == "deterministic_fixture_rehearsal"


def test_gitlab_source_benchmark_is_available_through_web_api(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    reference_root = Path(__file__).parents[1] / "data" / "reference-corpora"
    handoff = HandoffProofService(
        tmp_path / "handoff",
        reference_corpora_root=reference_root,
    )
    with TestClient(create_app(service, handoff_service=handoff)) as client:  # type: ignore[arg-type]
        created = client.post("/api/handoff/gitlab")
        rehearsed = client.post("/api/handoff/cases/gitlab-runbooks-handover-benchmark/rehearse")
        report = client.post(
            "/api/handoff/cases/gitlab-runbooks-handover-benchmark/benchmark-report"
        )

    assert created.status_code == 200
    assert created.json()["case"]["provenance"]["integrity_verified"] is True
    assert created.json()["case"]["benchmark_status"] == "source_derived_review_pending"
    assert rehearsed.status_code == 200
    assert rehearsed.json()["mode"] == "source_derived_benchmark_rehearsal"
    assert rehearsed.json()["all_patterns_match"] is True
    assert report.status_code == 400
    assert "missing:" in report.json()["detail"]


def test_phase_seven_review_packet_is_available_through_web_api(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    reference_root = Path(__file__).parents[1] / "data" / "reference-corpora"
    handoff = HandoffProofService(
        tmp_path / "handoff",
        reference_corpora_root=reference_root,
    )
    handoff.initialize_gitlab_benchmark(reset=True)
    with TestClient(create_app(service, handoff_service=handoff)) as client:  # type: ignore[arg-type]
        created = client.post("/api/handoff/cases/gitlab-runbooks-handover-benchmark/review-packet")
        review_id = created.json()["reviews"][0]["review_id"]
        refused = client.post(
            f"/api/handoff/reviews/{review_id}",
            json={
                "reviewer": "Independent Reviewer",
                "decision": "approved",
                "notes": "Only one check completed.",
                "checklist": {
                    "source_alignment": True,
                    "start_state_realism": False,
                    "reference_actions_complete": False,
                    "verifier_criteria_valid": False,
                },
            },
        )

    assert created.status_code == 200
    assert created.json()["packet"]["complete"] is False
    assert len(created.json()["reviews"]) == 4
    assert refused.status_code == 400
    assert "every independent-review check" in refused.json()["detail"]


def test_live_agent_endpoint_reports_missing_runner_as_runtime_failure(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    handoff = HandoffProofService(tmp_path / "handoff")
    handoff.initialize_synthetic_case()
    with TestClient(create_app(service, handoff_service=handoff)) as client:  # type: ignore[arg-type]
        response = client.post(
            "/api/handoff/cases/synthetic-ledger-service-handover/agent-experiments",
            params={"task_id": "task-control-queue"},
        )

    assert response.status_code == 503
    assert "runner is not configured" in response.json()["detail"]


def test_phase_five_routes_report_missing_records(tmp_path: Path) -> None:
    service = StubService(tmp_path)
    handoff = HandoffProofService(tmp_path / "handoff")
    with TestClient(create_app(service, handoff_service=handoff)) as client:  # type: ignore[arg-type]
        question = client.post("/api/handoff/experiments/missing/questions")
        answer = client.post(
            "/api/handoff/questions/missing/answers",
            json={
                "answer_text": "procedure",
                "source_reference": "runbook",
                "expert_name": "expert",
            },
        )
        approval = client.post(
            "/api/handoff/answers/missing/approve",
            json={"approved_by": "owner"},
        )
        replay = client.post("/api/handoff/patches/missing/replay")

    assert question.status_code == 404
    assert answer.status_code == 404
    assert approval.status_code == 404
    assert replay.status_code == 404
