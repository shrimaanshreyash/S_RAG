from datetime import UTC, datetime
from pathlib import Path

from srag.chunking import StructureAwareChunker
from srag.domain import CanonicalBlock, CanonicalDocument


def make_document() -> CanonicalDocument:
    return CanonicalDocument(
        document_id="doc123",
        filename="policy.pdf",
        source_path=Path("policy.pdf"),
        sha256="a" * 64,
        size_bytes=100,
        title="Policy",
        parser_name="test",
        parser_version="1",
        parsed_at=datetime.now(UTC),
        blocks=[
            CanonicalBlock(
                block_id="b1",
                kind="section_header",
                text="Authentication",
                section="Authentication",
                page_numbers=[1],
            ),
            CanonicalBlock(
                block_id="b2",
                kind="text",
                text="Passwords must contain multiple character classes. " * 10,
                section="Authentication",
                page_numbers=[1, 2],
            ),
            CanonicalBlock(
                block_id="b3",
                kind="section_header",
                text="Remote Access",
                section="Remote Access",
                page_numbers=[3],
            ),
            CanonicalBlock(
                block_id="b4",
                kind="text",
                text="Remote connections require a managed device.",
                section="Remote Access",
                page_numbers=[3],
            ),
        ],
    )


def test_chunker_preserves_provenance_and_section_boundaries() -> None:
    chunks = StructureAwareChunker(chunk_size_tokens=100, overlap_tokens=10).chunk(make_document())

    assert len(chunks) >= 2
    assert chunks[0].document_id == "doc123"
    assert chunks[0].page_numbers
    assert chunks[-1].section == "Remote Access"
    assert "managed device" in chunks[-1].text
