from srag.domain import Chunk, SearchHit
from srag.generation import OllamaGenerator


def test_context_contains_stable_citation_metadata() -> None:
    hit = SearchHit(
        rank=1,
        score=0.9,
        chunk=Chunk(
            chunk_id="doc:c1",
            document_id="doc",
            filename="manual.pdf",
            text="The system must remain offline.",
            section="Security",
            page_numbers=[4],
            block_ids=["b1"],
            token_estimate=8,
        ),
    )

    context, citations = OllamaGenerator._build_context([hit])

    assert "[S1]" in context
    assert "manual.pdf" in context
    assert citations[0].page_numbers == [4]


def test_context_exposes_typesafe_conflict_label() -> None:
    hit = SearchHit(
        rank=3,
        score=0.75,
        chunk=Chunk(
            chunk_id="doc:c3",
            document_id="doc",
            filename="manual.pdf",
            text="The stated premise is not correct.",
            section="Correction",
            page_numbers=[8],
            block_ids=["b3"],
            token_estimate=8,
        ),
    )

    context, _citations = OllamaGenerator._build_context([hit], {"doc:c3": "conflicting_evidence"})

    assert "classification: conflicting_evidence" in context
