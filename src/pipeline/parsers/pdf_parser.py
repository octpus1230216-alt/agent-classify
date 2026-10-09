"""PDF 解析器：基于 pdfplumber 提取文本与表格。"""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from pipeline.models import ParsedDocument


def parse_pdf(path: str | Path) -> ParsedDocument:
    """解析 PDF，合并页面文本与表格。"""
    paragraphs: list[str] = []
    tables: list[list[list[str]]] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                paragraphs.extend(
                    line.strip() for line in text.splitlines() if line.strip()
                )
            for table in page.extract_tables() or []:
                clean = [[str(c).strip() if c else "" for c in row] for row in table]
                tables.append(clean)
                for row in clean:
                    paragraphs.extend(c for c in row if c)

    raw_text = "\n".join(paragraphs)
    fields = _extract_fields(paragraphs)
    return ParsedDocument(
        file_path=Path(path),
        raw_text=raw_text,
        fields=fields,
        tables=tables,
    )


def _extract_fields(lines: list[str]) -> dict:
    """简易键值提取（占位实现）。"""
    fields: dict[str, str] = {}
    for line in lines:
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if key and value:
                fields[key] = value
    return fields
