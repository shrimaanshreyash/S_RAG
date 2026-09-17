from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from ollama import Client
from pydantic import BaseModel, Field

from srag.config import SUPPORTED_EXTENSIONS
from srag.handoffproof.domain import ReviewChecklist, ReviewDecision
from srag.handoffproof.factory import create_handoff_service
from srag.handoffproof.service import HandoffProofService
from srag.service import RagService


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class ExpertAnswerRequest(BaseModel):
    answer_text: str = Field(min_length=1, max_length=10_000)
    source_reference: str = Field(min_length=1, max_length=2_000)
    expert_name: str = Field(min_length=1, max_length=200)


class ExpertApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=1, max_length=200)


class BenchmarkReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=200)
    decision: ReviewDecision
    notes: str = Field(default="", max_length=5_000)
    checklist: ReviewChecklist


def _document_summary(document: Any, chunk_count: int) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "title": document.title,
        "size_bytes": document.size_bytes,
        "parser": f"{document.parser_name} {document.parser_version}",
        "parsed_at": document.parsed_at.isoformat(),
        "blocks": len(document.blocks),
        "chunks": chunk_count,
    }


def _save_upload(upload: UploadFile, service: RagService) -> Path:
    filename = Path(upload.filename or "document").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {suffix or '<none>'}")

    target_dir = service.settings.data_dir / "uploads" / uuid4().hex
    target_dir.mkdir(parents=True, exist_ok=False)
    target = target_dir / filename
    limit = service.settings.max_file_size_mb * 1024 * 1024
    written = 0
    with target.open("wb") as destination:
        while chunk := upload.file.read(1024 * 1024):
            written += len(chunk)
            if written > limit:
                destination.close()
                shutil.rmtree(target_dir)
                raise ValueError(
                    f"{filename} exceeds the {service.settings.max_file_size_mb} MB file limit"
                )
            destination.write(chunk)
    return target


def create_app(
    service: RagService | None = None,
    handoff_service: HandoffProofService | None = None,
) -> FastAPI:
    app = FastAPI(title="S/RAG local workbench", docs_url=None, redoc_url=None)
    app.state.service = service or RagService()
    app.state.handoff = handoff_service or create_handoff_service(app.state.service.settings)
    app.state.pipeline_lock = asyncio.Lock()
    app.state.handoff_lock = asyncio.Lock()
    web_root = Path(__file__).parent / "web"
    app.mount("/assets", StaticFiles(directory=web_root), name="assets")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(web_root / "index.html")

    @app.get("/api/status")
    async def status(request: Request) -> dict[str, Any]:
        rag: RagService = request.app.state.service
        settings = rag.settings
        documents = rag.artifacts.list_documents()
        try:
            models = await run_in_threadpool(
                lambda: Client(host=settings.ollama_host).list().models
            )
            names = {model.model for model in models}
            ollama_ready = True
        except Exception:  # noqa: BLE001 - runtime health must degrade to an offline state
            names = set()
            ollama_ready = False
        return {
            "ollama_ready": ollama_ready,
            "generation_model": settings.generation_model,
            "generation_ready": settings.generation_model in names,
            "embedding_model": settings.embedding_model,
            "embedding_ready": settings.embedding_model in names,
            "max_file_size_mb": settings.max_file_size_mb,
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
            "index": {"documents": len(documents), "chunks": rag.index.count()},
            "documents": [
                _document_summary(
                    document, len(rag.index.chunks_for_document(document.document_id))
                )
                for document in documents
            ],
        }

    @app.get("/api/documents/{document_id}")
    async def inspect_document(document_id: str, request: Request) -> dict[str, Any]:
        rag: RagService = request.app.state.service
        try:
            document = rag.artifacts.load_document(document_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Document not found") from error
        chunks = rag.index.chunks_for_document(document_id)
        return {
            "document": _document_summary(document, len(chunks)),
            "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        }

    @app.post("/api/documents")
    async def ingest_documents(
        request: Request,
        files: Annotated[list[UploadFile], File(description="Documents to index")],
    ) -> dict[str, Any]:
        if not files:
            raise HTTPException(status_code=400, detail="Select at least one document")
        rag: RagService = request.app.state.service
        saved_paths: list[Path] = []
        try:
            for upload in files:
                saved_paths.append(await run_in_threadpool(_save_upload, upload, rag))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            for upload in files:
                await upload.close()

        results: list[dict[str, Any]] = []
        async with request.app.state.pipeline_lock:
            for path in saved_paths:
                try:
                    result = await run_in_threadpool(rag.ingest_file, path)
                except Exception as error:  # noqa: BLE001 - report failure per uploaded file
                    results.append({"filename": path.name, "error": str(error)})
                    continue
                results.append(
                    {
                        "document": _document_summary(result.document, len(result.chunks)),
                        "metrics": result.metrics.model_dump(mode="json"),
                    }
                )
        return {"results": results}

    @app.post("/api/ask")
    async def ask(payload: AskRequest, request: Request) -> dict[str, Any]:
        rag: RagService = request.app.state.service
        try:
            async with request.app.state.pipeline_lock:
                result = await run_in_threadpool(rag.ask, payload.question, payload.top_k)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=503, detail=f"Local pipeline failed: {error}"
            ) from error
        return result.model_dump(mode="json")

    @app.get("/api/handoff/cases")
    async def list_handoff_cases(request: Request) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        return {
            "cases": [case.model_dump(mode="json") for case in handoff.list_cases()],
            "phase": "agent_execution_ready",
        }

    @app.post("/api/handoff/synthetic")
    async def initialize_synthetic_handoff(
        request: Request,
        reset: bool = False,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        bundle = await run_in_threadpool(lambda: handoff.initialize_synthetic_case(reset=reset))
        return bundle.model_dump(mode="json")

    @app.post("/api/handoff/gitlab")
    async def initialize_gitlab_handoff(
        request: Request,
        reset: bool = False,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            bundle = await run_in_threadpool(
                lambda: handoff.initialize_gitlab_benchmark(reset=reset)
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return bundle.model_dump(mode="json")

    @app.get("/api/handoff/cases/{case_id}")
    async def inspect_handoff_case(case_id: str, request: Request) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            bundle = handoff.get_case(case_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Handoff case not found") from error
        return bundle.model_dump(mode="json")

    @app.post("/api/handoff/cases/{case_id}/rehearse")
    async def rehearse_handoff_case(
        case_id: str,
        request: Request,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            result = await run_in_threadpool(lambda: handoff.rehearse_case(case_id, task_id))
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Handoff case not found") from error
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Handoff task not found") from error
        return result.model_dump(mode="json")

    @app.post("/api/handoff/cases/{case_id}/agent-experiments")
    async def run_handoff_agent_experiment(
        case_id: str,
        task_id: str,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            async with request.app.state.handoff_lock:
                result = await run_in_threadpool(lambda: handoff.run_agent_task(case_id, task_id))
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Handoff case not found") from error
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Handoff task not found") from error
        except Exception as error:
            raise HTTPException(
                status_code=503,
                detail=f"Local successor-agent experiment failed: {error}",
            ) from error
        return result.model_dump(mode="json")

    @app.get("/api/handoff/runs")
    async def list_handoff_runs(
        request: Request,
        case_id: str | None = None,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        return {"runs": [run.model_dump(mode="json") for run in handoff.list_runs(case_id)]}

    @app.get("/api/handoff/runs/{run_id}")
    async def inspect_handoff_run(run_id: str, request: Request) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            run = handoff.get_run(run_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Handoff run not found") from error
        return run.model_dump(mode="json")

    @app.post("/api/handoff/cases/{case_id}/benchmark-report")
    async def create_handoff_benchmark_report(
        case_id: str,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            report = await run_in_threadpool(lambda: handoff.create_benchmark_report(case_id))
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Handoff case not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return report.model_dump(mode="json")

    @app.post("/api/handoff/cases/{case_id}/review-packet")
    async def create_handoff_review_packet(
        case_id: str,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            packet = handoff.create_review_packet(case_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Handoff case not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        reviews = [
            review.model_dump(mode="json")
            for review in handoff.list_reviews(case_id)
            if review.packet_id == packet.packet_id
        ]
        return {"packet": packet.model_dump(mode="json"), "reviews": reviews}

    @app.get("/api/handoff/reviews")
    async def list_handoff_reviews(
        request: Request,
        case_id: str | None = None,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        return {
            "reviews": [review.model_dump(mode="json") for review in handoff.list_reviews(case_id)]
        }

    @app.post("/api/handoff/reviews/{review_id}")
    async def submit_handoff_review(
        review_id: str,
        payload: BenchmarkReviewRequest,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            packet = handoff.submit_benchmark_review(
                review_id,
                payload.reviewer,
                payload.decision,
                payload.notes,
                payload.checklist,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Review not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return packet.model_dump(mode="json")

    @app.post("/api/handoff/experiments/{experiment_id}/questions")
    async def create_expert_questions(
        experiment_id: str,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            questions = handoff.create_expert_questions(experiment_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Agent experiment not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"questions": [question.model_dump(mode="json") for question in questions]}

    @app.get("/api/handoff/questions")
    async def list_expert_questions(
        request: Request,
        case_id: str | None = None,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        return {
            "questions": [
                question.model_dump(mode="json") for question in handoff.list_questions(case_id)
            ]
        }

    @app.post("/api/handoff/questions/{question_id}/answers")
    async def submit_expert_answer(
        question_id: str,
        payload: ExpertAnswerRequest,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            answer = handoff.submit_expert_answer(
                question_id,
                payload.answer_text,
                payload.source_reference,
                payload.expert_name,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Expert question not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return answer.model_dump(mode="json")

    @app.post("/api/handoff/answers/{answer_id}/approve")
    async def approve_expert_answer(
        answer_id: str,
        payload: ExpertApprovalRequest,
        request: Request,
    ) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            patch = handoff.approve_expert_answer(answer_id, payload.approved_by)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Expert answer not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return patch.model_dump(mode="json")

    @app.post("/api/handoff/patches/{patch_id}/replay")
    async def replay_approved_patch(patch_id: str, request: Request) -> dict[str, Any]:
        handoff: HandoffProofService = request.app.state.handoff
        try:
            async with request.app.state.handoff_lock:
                replay = await run_in_threadpool(lambda: handoff.replay_patch(patch_id))
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Patch or source experiment not found"
            ) from error
        except (KeyError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return replay.model_dump(mode="json")

    return app


app = create_app()
