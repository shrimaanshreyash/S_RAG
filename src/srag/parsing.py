from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc.items.table.table import TableItem
from docling_core.types.doc.items.text import TextItem
from docling_core.types.doc.labels import DocItemLabel

from srag.domain import CanonicalBlock, CanonicalDocument


class DocumentTooLargeError(ValueError):
    pass


class DoclingParser:
    """Convert supported files into our parser-independent canonical schema."""

    def __init__(
        self,
        max_file_size_mb: int = 25,
        converter: DocumentConverter | None = None,
    ) -> None:
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.converter = converter or DocumentConverter()

    def parse(self, source: Path) -> tuple[CanonicalDocument, str]:
        source = source.resolve()
        size_bytes = source.stat().st_size
        if size_bytes > self.max_file_size_bytes:
            raise DocumentTooLargeError(
                f"{source.name} is {size_bytes / 1024 / 1024:.1f} MB; "
                f"configured maximum is {self.max_file_size_bytes / 1024 / 1024:.0f} MB"
            )

        digest = self._sha256(source)
        document_id = digest[:16]
        result = self.converter.convert(str(source))
        parsed = result.document

        blocks: list[CanonicalBlock] = []
        current_section: str | None = None
        title: str | None = None
        ignored_labels = {DocItemLabel.PAGE_HEADER, DocItemLabel.PAGE_FOOTER}

        for item, _level in parsed.iterate_items():
            text: str | None = None
            label = getattr(item, "label", None)

            if isinstance(item, TextItem):
                if label in ignored_labels:
                    continue
                text = item.text.strip()
            elif isinstance(item, TableItem):
                text = item.export_to_markdown(doc=parsed).strip()

            if not text:
                continue

            kind = label.value if label is not None else type(item).__name__.lower()
            if label == DocItemLabel.TITLE and title is None:
                title = text
                current_section = text
            elif label == DocItemLabel.SECTION_HEADER:
                current_section = text

            page_numbers = sorted(
                {
                    int(prov.page_no)
                    for prov in getattr(item, "prov", [])
                    if getattr(prov, "page_no", None) is not None
                }
            )
            blocks.append(
                CanonicalBlock(
                    block_id=f"{document_id}:b{len(blocks):06d}",
                    kind=kind,
                    text=text,
                    section=current_section,
                    page_numbers=page_numbers,
                    source_ref=str(getattr(item, "self_ref", "")) or None,
                )
            )

        if not blocks:
            raise ValueError(f"Docling produced no textual blocks for {source.name}")

        document = CanonicalDocument(
            document_id=document_id,
            filename=source.name,
            source_path=source,
            sha256=digest,
            size_bytes=size_bytes,
            title=title or source.stem,
            parser_name="docling",
            parser_version=version("docling"),
            parsed_at=datetime.now(UTC),
            blocks=blocks,
        )
        return document, parsed.export_to_markdown()

    @staticmethod
    def _sha256(source: Path) -> str:
        digest = hashlib.sha256()
        with source.open("rb") as handle:
            for piece in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(piece)
        return digest.hexdigest()
