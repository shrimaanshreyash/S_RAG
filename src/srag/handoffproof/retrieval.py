from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Protocol

from srag.domain import Chunk
from srag.handoffproof.domain import (
    CorpusMode,
    HandoffCaseBundle,
    KnowledgeFact,
    RetrievalMode,
    TaskDefinition,
)
from srag.interfaces import Embedder
from srag.storage import LocalVectorIndex


class EvidenceRetriever(Protocol):
    def retrieve(
        self,
        bundle: HandoffCaseBundle,
        task: TaskDefinition,
        corpus_mode: CorpusMode,
        retrieval_mode: RetrievalMode,
    ) -> list[KnowledgeFact]: ...


class HandoffEvidenceRetriever:
    """Scoped retrieval over approved handover facts using the existing local vector index."""

    def __init__(self, root: Path, embedder: Embedder, top_k: int = 4) -> None:
        self.root = root
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(
        self,
        bundle: HandoffCaseBundle,
        task: TaskDefinition,
        corpus_mode: CorpusMode,
        retrieval_mode: RetrievalMode,
    ) -> list[KnowledgeFact]:
        current_version = next(
            version
            for version in bundle.case.corpus_versions
            if version.version_id == bundle.case.current_corpus_version_id
        )
        current_fact_ids = set(current_version.fact_ids)
        corpus_facts = [
            fact
            for fact in bundle.facts
            if corpus_mode is CorpusMode.COMPLETE or fact.fact_id in current_fact_ids
        ]
        if retrieval_mode is RetrievalMode.ORACLE:
            fact_by_id = {fact.fact_id: fact for fact in corpus_facts}
            return [
                fact_by_id[fact_id] for fact_id in task.required_fact_ids if fact_id in fact_by_id
            ]

        eligible = [fact for fact in corpus_facts if fact.normal_retrieval_surfaces]
        if not eligible:
            return []
        fingerprint_source = "\n".join(
            f"{fact.fact_id}:{fact.source}:{fact.text}" for fact in eligible
        )
        fingerprint = sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
        index = LocalVectorIndex(self.root / bundle.case.case_id / fingerprint, self.embedder)
        if index.count() != len(eligible):
            chunks = [
                Chunk(
                    chunk_id=fact.fact_id,
                    document_id=f"{bundle.case.case_id}:{fingerprint}",
                    filename=fact.source.split("#", maxsplit=1)[0],
                    text=fact.text,
                    section=fact.title,
                    block_ids=[fact.fact_id],
                    token_estimate=max(1, len(fact.text) // 4),
                )
                for fact in eligible
            ]
            index.replace_document(f"{bundle.case.case_id}:{fingerprint}", chunks)
        query = f"{task.title}. {task.objective}"
        hits = index.search(query, min(self.top_k, len(eligible)))
        fact_by_id = {fact.fact_id: fact for fact in eligible}
        return [fact_by_id[hit.chunk.chunk_id] for hit in hits]
