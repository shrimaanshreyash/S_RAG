from __future__ import annotations

from pathlib import Path
from typing import Protocol

from srag.domain import CanonicalDocument, Chunk, EvidenceJudgment, SearchHit


class DocumentParser(Protocol):
    def parse(self, source: Path) -> tuple[CanonicalDocument, str]: ...


class Chunker(Protocol):
    def chunk(self, document: CanonicalDocument) -> list[Chunk]: ...


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class Retriever(Protocol):
    def replace_document(self, document_id: str, chunks: list[Chunk]) -> None: ...

    def search(self, query: str, top_k: int) -> list[SearchHit]: ...


class EvidenceJudge(Protocol):
    def judge(self, question: str, hits: list[SearchHit]) -> list[EvidenceJudgment]: ...
