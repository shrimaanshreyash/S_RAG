from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class CanonicalBlock(BaseModel):
    block_id: str
    kind: str
    text: str
    section: str | None = None
    page_numbers: list[int] = Field(default_factory=list)
    source_ref: str | None = None


class CanonicalDocument(BaseModel):
    schema_version: str = "1.0"
    document_id: str
    filename: str
    source_path: Path
    sha256: str
    size_bytes: int
    title: str
    parser_name: str
    parser_version: str
    parsed_at: datetime
    blocks: list[CanonicalBlock]


class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    text: str
    section: str | None = None
    page_numbers: list[int] = Field(default_factory=list)
    block_ids: list[str] = Field(default_factory=list)
    token_estimate: int


class SearchHit(BaseModel):
    rank: int
    score: float
    chunk: Chunk


class Citation(BaseModel):
    marker: str
    filename: str
    page_numbers: list[int] = Field(default_factory=list)
    section: str | None = None
    chunk_id: str


class EvidenceRoute(StrEnum):
    INCLUDE = "include"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    REVIEW = "review"
    EXCLUDE_INJECTION = "exclude_injection"
    EXCLUDE_IRRELEVANT = "exclude_irrelevant"
    EXCLUDE_WEAK = "exclude_weak"


class EvidenceJudgment(BaseModel):
    candidate_rank: int
    chunk_id: str
    filename: str = ""
    section: str | None = None
    retrieval_score: float = 0.0
    route: EvidenceRoute
    is_relevant: float = Field(ge=0.0, le=1.0)
    contains_answer_evidence: float = Field(ge=0.0, le=1.0)
    contradicts_query_premise: float = Field(ge=0.0, le=1.0)
    contains_prompt_injection: float = Field(ge=0.0, le=1.0)
    model: str
    policy_version: str
    latency_seconds: float = Field(ge=0.0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class AnswerMetrics(BaseModel):
    end_to_end_seconds: float = 0.0
    retrieval_seconds: float = 0.0
    query_embedding_seconds: float = 0.0
    similarity_search_seconds: float = 0.0
    embedding_model_load_seconds: float = 0.0
    embedding_eval_seconds: float = 0.0
    embedding_input_tokens: int = 0
    embedding_dimensions: int = 0
    generation_wall_seconds: float = 0.0
    time_to_first_token_seconds: float = 0.0
    ollama_total_seconds: float = 0.0
    model_load_seconds: float = 0.0
    prompt_eval_seconds: float = 0.0
    generation_eval_seconds: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    output_tokens_per_second: float = 0.0
    retrieved_chunks: int = 0
    context_characters: int = 0
    typesafe_wall_seconds: float = 0.0
    typesafe_input_tokens: int = 0
    typesafe_output_tokens: int = 0
    typesafe_candidates: int = 0
    typesafe_included: int = 0
    typesafe_conflicts: int = 0
    typesafe_review: int = 0
    typesafe_excluded: int = 0


class AnswerResult(BaseModel):
    question: str
    normalized_question: str
    hits: list[SearchHit]
    context: str
    answer: str
    citations: list[Citation]
    metrics: AnswerMetrics
    evidence_judgments: list[EvidenceJudgment] = Field(default_factory=list)


class IngestMetrics(BaseModel):
    total_seconds: float
    parse_seconds: float
    chunk_seconds: float
    artifact_write_seconds: float
    embedding_and_index_seconds: float
    document_size_mb: float
    canonical_blocks: int
    chunks_indexed: int
    characters_embedded: int
    chunks_per_second: float


class IngestResult(BaseModel):
    document: CanonicalDocument
    chunks: list[Chunk]
    canonical_path: Path
    markdown_path: Path
    metrics: IngestMetrics
