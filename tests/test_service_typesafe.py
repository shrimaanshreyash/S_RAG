from types import SimpleNamespace

from srag.domain import (
    AnswerMetrics,
    AnswerResult,
    Chunk,
    EvidenceJudgment,
    EvidenceRoute,
    SearchHit,
)
from srag.service import RagService


def _hit(rank: int) -> SearchHit:
    return SearchHit(
        rank=rank,
        score=1.0 - rank / 100,
        chunk=Chunk(
            chunk_id=f"chunk-{rank}",
            document_id="document",
            filename="runbook.md",
            section=f"Section {rank}",
            text=f"Passage {rank}",
            block_ids=[f"block-{rank}"],
            token_estimate=3,
        ),
    )


class FakeIndex:
    last_embedding_seconds = 0.1
    last_similarity_seconds = 0.01

    def __init__(self) -> None:
        self.requested_top_k = 0

    def search(self, _question: str, top_k: int) -> list[SearchHit]:
        self.requested_top_k = top_k
        return [_hit(rank) for rank in range(1, top_k + 1)]


class FakeJudge:
    def judge(self, _question: str, hits: list[SearchHit]) -> list[EvidenceJudgment]:
        return [
            EvidenceJudgment(
                candidate_rank=hit.rank,
                chunk_id=hit.chunk.chunk_id,
                filename=hit.chunk.filename,
                section=hit.chunk.section,
                retrieval_score=hit.score,
                route=(
                    EvidenceRoute.INCLUDE
                    if 7 <= hit.rank <= 11
                    else EvidenceRoute.EXCLUDE_WEAK
                ),
                is_relevant=0.9,
                contains_answer_evidence=0.9 if 7 <= hit.rank <= 11 else 0.1,
                contradicts_query_premise=0.1,
                contains_prompt_injection=0.1,
                model="jev-test",
                policy_version="test-policy",
                latency_seconds=0.1,
                input_tokens=10,
                output_tokens=2,
            )
            for hit in hits
        ]


class FakeGenerator:
    def __init__(self) -> None:
        self.hits: list[SearchHit] = []
        self.routes: dict[str, str] = {}

    def answer(
        self,
        question: str,
        hits: list[SearchHit],
        evidence_routes: dict[str, str],
    ) -> AnswerResult:
        self.hits = hits
        self.routes = evidence_routes
        return AnswerResult(
            question=question,
            normalized_question=question,
            hits=hits,
            context="context",
            answer="answer",
            citations=[],
            metrics=AnswerMetrics(retrieved_chunks=len(hits)),
        )


def test_typesafe_scores_full_shortlist_then_caps_approved_sources() -> None:
    service = RagService.__new__(RagService)
    service.settings = SimpleNamespace(default_top_k=4, typesafe_candidate_top_k=12)
    service.index = FakeIndex()
    service.evidence_judge = FakeJudge()
    service.generator = FakeGenerator()
    service.embedder = SimpleNamespace(
        last_metrics=SimpleNamespace(
            load_seconds=0.0,
            eval_seconds=0.0,
            input_tokens=0,
            dimensions=0,
        )
    )

    result = service.ask("question", top_k=4)

    assert service.index.requested_top_k == 12
    assert [hit.rank for hit in service.generator.hits] == [7, 8, 9, 10]
    assert set(service.generator.routes) == {"chunk-7", "chunk-8", "chunk-9", "chunk-10"}
    assert result.metrics.typesafe_candidates == 12
    assert result.metrics.typesafe_included == 5


def test_without_typesafe_the_requested_top_k_is_used_directly() -> None:
    service = RagService.__new__(RagService)
    service.settings = SimpleNamespace(default_top_k=4, typesafe_candidate_top_k=12)
    service.index = FakeIndex()
    service.evidence_judge = None
    service.generator = FakeGenerator()
    service.embedder = SimpleNamespace(
        last_metrics=SimpleNamespace(
            load_seconds=0.0,
            eval_seconds=0.0,
            input_tokens=0,
            dimensions=0,
        )
    )

    service.ask("question", top_k=3)

    assert service.index.requested_top_k == 3
    assert [hit.rank for hit in service.generator.hits] == [1, 2, 3]
