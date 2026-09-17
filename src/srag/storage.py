from __future__ import annotations

import tempfile
from pathlib import Path
from time import perf_counter
from typing import cast

import numpy as np
import orjson
from numpy.typing import NDArray

from srag.domain import CanonicalDocument, Chunk, SearchHit
from srag.interfaces import Embedder


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save_document(
        self,
        document: CanonicalDocument,
        markdown: str,
    ) -> tuple[Path, Path]:
        target = self.root / "documents" / document.document_id
        target.mkdir(parents=True, exist_ok=True)
        canonical_path = target / "canonical.json"
        markdown_path = target / "document.md"
        self._atomic_write(
            canonical_path,
            document.model_dump_json(indent=2).encode("utf-8"),
        )
        self._atomic_write(markdown_path, markdown.encode("utf-8"))
        return canonical_path, markdown_path

    def load_document(self, document_id: str) -> CanonicalDocument:
        path = self.root / "documents" / document_id / "canonical.json"
        return CanonicalDocument.model_validate_json(path.read_bytes())

    def list_documents(self) -> list[CanonicalDocument]:
        documents: list[CanonicalDocument] = []
        for path in sorted((self.root / "documents").glob("*/canonical.json")):
            documents.append(CanonicalDocument.model_validate_json(path.read_bytes()))
        return documents

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(path)


class LocalVectorIndex:
    """Transparent cosine-similarity index for a small local document collection."""

    def __init__(self, root: Path, embedder: Embedder) -> None:
        self.root = root
        self.embedder = embedder
        self.chunks_path = root / "chunks.json"
        self.vectors_path = root / "vectors.npy"
        self.last_embedding_seconds = 0.0
        self.last_similarity_seconds = 0.0

    def replace_document(self, document_id: str, chunks: list[Chunk]) -> None:
        existing_chunks, existing_vectors = self._load()
        keep = [i for i, chunk in enumerate(existing_chunks) if chunk.document_id != document_id]
        retained_chunks = [existing_chunks[i] for i in keep]
        retained_vectors = (
            existing_vectors[keep]
            if keep and existing_vectors.size
            else np.empty((0, 0), dtype=np.float32)
        )

        new_vectors = self._normalize(
            np.asarray(
                self.embedder.embed_documents([chunk.text for chunk in chunks]),
                dtype=np.float32,
            )
        )
        if retained_vectors.size and retained_vectors.shape[1] != new_vectors.shape[1]:
            raise ValueError(
                "Embedding dimension changed. Remove the index or re-ingest every document."
            )

        all_chunks = retained_chunks + chunks
        all_vectors = (
            np.vstack([retained_vectors, new_vectors]) if retained_vectors.size else new_vectors
        )
        self._save(all_chunks, all_vectors)

    def search(self, query: str, top_k: int) -> list[SearchHit]:
        chunks, vectors = self._load()
        if not chunks or not vectors.size:
            raise ValueError("The index is empty. Ingest at least one document first.")
        embedding_started = perf_counter()
        query_vector = self._normalize(
            np.asarray([self.embedder.embed_query(query)], dtype=np.float32)
        )[0]
        self.last_embedding_seconds = perf_counter() - embedding_started
        if vectors.shape[1] != query_vector.shape[0]:
            raise ValueError("Query embedding dimension does not match the stored index.")
        similarity_started = perf_counter()
        scores = vectors @ query_vector
        indices = np.argsort(scores)[::-1][: min(top_k, len(chunks))]
        hits = [
            SearchHit(rank=rank, score=float(scores[index]), chunk=chunks[index])
            for rank, index in enumerate(indices, start=1)
        ]
        self.last_similarity_seconds = perf_counter() - similarity_started
        return hits

    def chunks_for_document(self, document_id: str) -> list[Chunk]:
        chunks, _vectors = self._load()
        return [chunk for chunk in chunks if chunk.document_id == document_id]

    def count(self) -> int:
        chunks, _vectors = self._load()
        return len(chunks)

    def _load(self) -> tuple[list[Chunk], np.ndarray]:
        if not self.chunks_path.exists() or not self.vectors_path.exists():
            return [], np.empty((0, 0), dtype=np.float32)
        raw_chunks = orjson.loads(self.chunks_path.read_bytes())
        chunks = [Chunk.model_validate(item) for item in raw_chunks]
        vectors = np.load(self.vectors_path, allow_pickle=False).astype(np.float32)
        return chunks, vectors

    def _save(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        chunk_bytes = orjson.dumps(
            [chunk.model_dump(mode="json") for chunk in chunks],
            option=orjson.OPT_INDENT_2,
        )
        ArtifactStore._atomic_write(self.chunks_path, chunk_bytes)
        with tempfile.NamedTemporaryFile(
            dir=self.root,
            suffix=".npy",
            delete=False,
        ) as handle:
            np.save(handle, vectors.astype(np.float32), allow_pickle=False)
            temporary = Path(handle.name)
        temporary.replace(self.vectors_path)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> NDArray[np.float32]:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return cast(NDArray[np.float32], vectors / norms)
