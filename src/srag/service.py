from __future__ import annotations

from pathlib import Path
from time import perf_counter

from srag.chunking import StructureAwareChunker
from srag.config import SUPPORTED_EXTENSIONS, Settings
from srag.domain import AnswerResult, EvidenceRoute, IngestMetrics, IngestResult
from srag.embedding import OllamaEmbedder
from srag.generation import OllamaGenerator
from srag.parsing import DoclingParser
from srag.storage import ArtifactStore, LocalVectorIndex
from srag.typesafe_evidence import TypeSafeEvidenceJudge


class RagService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.parser = DoclingParser(max_file_size_mb=self.settings.max_file_size_mb)
        self.chunker = StructureAwareChunker(
            chunk_size_tokens=self.settings.chunk_size_tokens,
            overlap_tokens=self.settings.chunk_overlap_tokens,
        )
        self.embedder = OllamaEmbedder(
            model=self.settings.embedding_model,
            host=self.settings.ollama_host,
        )
        self.artifacts = ArtifactStore(self.settings.artifacts_dir)
        self.index = LocalVectorIndex(self.settings.index_dir, self.embedder)
        self.generator = OllamaGenerator(
            model=self.settings.generation_model,
            host=self.settings.ollama_host,
            context_window=self.settings.generation_context_tokens,
            max_output_tokens=self.settings.max_output_tokens,
        )
        self.evidence_judge = None
        if self.settings.typesafe_enabled:
            secret = self.settings.typesafe_api_key
            self.evidence_judge = TypeSafeEvidenceJudge(
                api_key=secret.get_secret_value() if secret is not None else "",
                model=self.settings.typesafe_model,
                timeout_seconds=self.settings.typesafe_timeout_seconds,
                max_workers=self.settings.typesafe_max_workers,
            )

    def ingest_file(self, source: Path) -> IngestResult:
        started = perf_counter()
        if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {source.suffix or '<none>'}")

        stage_started = perf_counter()
        document, markdown = self.parser.parse(source)
        parse_seconds = perf_counter() - stage_started

        stage_started = perf_counter()
        chunks = self.chunker.chunk(document)
        chunk_seconds = perf_counter() - stage_started

        stage_started = perf_counter()
        canonical_path, markdown_path = self.artifacts.save_document(document, markdown)
        artifact_write_seconds = perf_counter() - stage_started

        stage_started = perf_counter()
        self.index.replace_document(document.document_id, chunks)
        embedding_and_index_seconds = perf_counter() - stage_started
        total_seconds = perf_counter() - started
        return IngestResult(
            document=document,
            chunks=chunks,
            canonical_path=canonical_path,
            markdown_path=markdown_path,
            metrics=IngestMetrics(
                total_seconds=total_seconds,
                parse_seconds=parse_seconds,
                chunk_seconds=chunk_seconds,
                artifact_write_seconds=artifact_write_seconds,
                embedding_and_index_seconds=embedding_and_index_seconds,
                document_size_mb=document.size_bytes / 1024 / 1024,
                canonical_blocks=len(document.blocks),
                chunks_indexed=len(chunks),
                characters_embedded=sum(len(chunk.text) for chunk in chunks),
                chunks_per_second=(
                    len(chunks) / embedding_and_index_seconds
                    if embedding_and_index_seconds > 0
                    else 0.0
                ),
            ),
        )

    def ingest_path(self, source: Path) -> list[IngestResult]:
        if source.is_file():
            candidates = [source]
        elif source.is_dir():
            candidates = sorted(
                path
                for path in source.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )
        else:
            raise FileNotFoundError(source)
        if not candidates:
            raise ValueError(f"No supported documents found at {source}")
        return [self.ingest_file(candidate) for candidate in candidates]

    def ask(self, question: str, top_k: int | None = None) -> AnswerResult:
        started = perf_counter()
        normalized = " ".join(question.split())
        if not normalized:
            raise ValueError("Question cannot be empty")
        retrieval_started = perf_counter()
        result_limit = top_k or self.settings.default_top_k
        candidate_top_k = (
            max(result_limit, self.settings.typesafe_candidate_top_k)
            if self.evidence_judge is not None
            else result_limit
        )
        hits = self.index.search(normalized, candidate_top_k)
        retrieval_seconds = perf_counter() - retrieval_started
        judgments = []
        evidence_routes: dict[str, str] = {}
        selected_hits = hits
        typesafe_started = perf_counter()
        if self.evidence_judge is not None:
            judgments = self.evidence_judge.judge(normalized, hits)
            routes_by_chunk = {item.chunk_id: item.route for item in judgments}
            selected_hits = [
                hit
                for hit in hits
                if routes_by_chunk[hit.chunk.chunk_id]
                in {EvidenceRoute.INCLUDE, EvidenceRoute.CONFLICTING_EVIDENCE}
            ][:result_limit]
            selected_ids = {hit.chunk.chunk_id for hit in selected_hits}
            evidence_routes = {
                item.chunk_id: item.route.value
                for item in judgments
                if item.chunk_id in selected_ids
                if item.route in {EvidenceRoute.INCLUDE, EvidenceRoute.CONFLICTING_EVIDENCE}
            }
        typesafe_seconds = (
            perf_counter() - typesafe_started if self.evidence_judge is not None else 0.0
        )
        result = self.generator.answer(question, selected_hits, evidence_routes)
        result.evidence_judgments = judgments
        result.metrics.retrieval_seconds = retrieval_seconds
        result.metrics.query_embedding_seconds = self.index.last_embedding_seconds
        result.metrics.similarity_search_seconds = self.index.last_similarity_seconds
        embedding_metrics = self.embedder.last_metrics
        result.metrics.embedding_model_load_seconds = embedding_metrics.load_seconds
        result.metrics.embedding_eval_seconds = embedding_metrics.eval_seconds
        result.metrics.embedding_input_tokens = embedding_metrics.input_tokens
        result.metrics.embedding_dimensions = embedding_metrics.dimensions
        result.metrics.typesafe_wall_seconds = typesafe_seconds
        result.metrics.typesafe_input_tokens = sum(item.input_tokens for item in judgments)
        result.metrics.typesafe_output_tokens = sum(item.output_tokens for item in judgments)
        result.metrics.typesafe_candidates = len(judgments)
        result.metrics.typesafe_included = sum(
            item.route is EvidenceRoute.INCLUDE for item in judgments
        )
        result.metrics.typesafe_conflicts = sum(
            item.route is EvidenceRoute.CONFLICTING_EVIDENCE for item in judgments
        )
        result.metrics.typesafe_review = sum(
            item.route is EvidenceRoute.REVIEW for item in judgments
        )
        result.metrics.typesafe_excluded = sum(
            item.route
            in {
                EvidenceRoute.EXCLUDE_INJECTION,
                EvidenceRoute.EXCLUDE_IRRELEVANT,
                EvidenceRoute.EXCLUDE_WEAK,
            }
            for item in judgments
        )
        result.metrics.end_to_end_seconds = perf_counter() - started
        return result
