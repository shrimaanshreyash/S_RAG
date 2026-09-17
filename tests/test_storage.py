from pathlib import Path
from typing import ClassVar

from srag.domain import Chunk
from srag.storage import LocalVectorIndex


class FakeEmbedder:
    vectors: ClassVar[dict[str, list[float]]] = {
        "alpha policy": [1.0, 0.0],
        "beta procedure": [0.0, 1.0],
        "find alpha": [0.9, 0.1],
    }

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.vectors[text] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.vectors[text]


def chunk(chunk_id: str, document_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id=document_id,
        filename=f"{document_id}.txt",
        text=text,
        page_numbers=[1],
        block_ids=["b1"],
        token_estimate=3,
    )


def test_index_search_and_document_replacement(tmp_path: Path) -> None:
    index = LocalVectorIndex(tmp_path, FakeEmbedder())
    index.replace_document("a", [chunk("a:c1", "a", "alpha policy")])
    index.replace_document("b", [chunk("b:c1", "b", "beta procedure")])

    hits = index.search("find alpha", top_k=2)
    assert hits[0].chunk.chunk_id == "a:c1"
    assert hits[0].score > hits[1].score

    index.replace_document("a", [chunk("a:c2", "a", "alpha policy")])
    assert {item.chunk_id for item in index.chunks_for_document("a")} == {"a:c2"}
    assert index.count() == 2
