from __future__ import annotations

import math
from dataclasses import dataclass

from srag.domain import CanonicalBlock, CanonicalDocument, Chunk


@dataclass(frozen=True)
class _Fragment:
    text: str
    block_id: str
    section: str | None
    page_numbers: list[int]


class StructureAwareChunker:
    """Chunk on document boundaries while retaining section and page provenance."""

    def __init__(self, chunk_size_tokens: int = 600, overlap_tokens: int = 80) -> None:
        if overlap_tokens >= chunk_size_tokens:
            raise ValueError("overlap_tokens must be smaller than chunk_size_tokens")
        self.max_chars = chunk_size_tokens * 4
        self.overlap_chars = overlap_tokens * 4

    def chunk(self, document: CanonicalDocument) -> list[Chunk]:
        fragments = [fragment for block in document.blocks for fragment in self._split_block(block)]
        chunks: list[Chunk] = []
        current: list[_Fragment] = []
        current_chars = 0

        for fragment in fragments:
            section_changed = bool(
                current
                and fragment.section
                and current[-1].section
                and fragment.section != current[-1].section
            )
            would_overflow = current_chars + len(fragment.text) + 2 > self.max_chars
            if current and (section_changed or would_overflow):
                chunks.append(self._build_chunk(document, current, len(chunks)))
                current = self._overlap_tail(current) if not section_changed else []
                current_chars = sum(len(part.text) + 2 for part in current)

            current.append(fragment)
            current_chars += len(fragment.text) + 2

        if current:
            chunks.append(self._build_chunk(document, current, len(chunks)))
        return chunks

    def _split_block(self, block: CanonicalBlock) -> list[_Fragment]:
        if len(block.text) <= self.max_chars:
            return [_Fragment(block.text, block.block_id, block.section, block.page_numbers)]

        words = block.text.split()
        pieces: list[str] = []
        current: list[str] = []
        length = 0
        for word in words:
            if current and length + len(word) + 1 > self.max_chars:
                pieces.append(" ".join(current))
                current = []
                length = 0
            current.append(word)
            length += len(word) + 1
        if current:
            pieces.append(" ".join(current))
        return [
            _Fragment(piece, block.block_id, block.section, block.page_numbers) for piece in pieces
        ]

    def _overlap_tail(self, fragments: list[_Fragment]) -> list[_Fragment]:
        if self.overlap_chars == 0:
            return []
        tail: list[_Fragment] = []
        length = 0
        for fragment in reversed(fragments):
            if tail and length + len(fragment.text) > self.overlap_chars:
                break
            tail.append(fragment)
            length += len(fragment.text)
        return list(reversed(tail))

    @staticmethod
    def _build_chunk(
        document: CanonicalDocument,
        fragments: list[_Fragment],
        chunk_index: int,
    ) -> Chunk:
        text = "\n\n".join(fragment.text for fragment in fragments).strip()
        return Chunk(
            chunk_id=f"{document.document_id}:c{chunk_index:05d}",
            document_id=document.document_id,
            filename=document.filename,
            text=text,
            section=next((f.section for f in fragments if f.section), None),
            page_numbers=sorted({page for f in fragments for page in f.page_numbers}),
            block_ids=list(dict.fromkeys(f.block_id for f in fragments)),
            token_estimate=max(1, math.ceil(len(text) / 4)),
        )
