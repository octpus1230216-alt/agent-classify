"""Stage 1 格式筛选测试：验证伪装扩展名被拦截。"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.models import PipelineItem
from pipeline.stages.s1_format_filter import FormatFilterStage


@pytest.fixture
def tmp_files(tmp_path: Path) -> dict[str, Path]:
    """构造 5 个测试文件（2 合法 + 3 伪装/非法）。"""
    # 合法 docx（PK 头）
    docx = tmp_path / "a.docx"
    docx.write_bytes(b"PK\x03\x04" + b"\x00" * 100)

    # 合法 pdf
    pdf = tmp_path / "b.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)

    # 伪装：txt 扩展名 -> 扩展名不被允许
    txt = tmp_path / "c.txt"
    txt.write_bytes(b"PK\x03\x04" + b"\x00" * 100)

    # 伪装：.docx 扩展名但实际是 PDF 头
    fake_docx = tmp_path / "d.docx"
    fake_docx.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)

    # 伪装：.pdf 扩展名但实际是 docx 头
    fake_pdf = tmp_path / "e.pdf"
    fake_pdf.write_bytes(b"PK\x03\x04" + b"\x00" * 100)

    return {
        "docx": docx,
        "pdf": pdf,
        "txt": txt,
        "fake_docx": fake_docx,
        "fake_pdf": fake_pdf,
    }


def _make_items(files: dict[str, Path]) -> list[PipelineItem]:
    return [PipelineItem(file_path=p, file_name=p.name) for p in files.values()]


def test_legit_files_pass(tmp_files):
    """合法的 docx 和 pdf 应通过。"""
    stage = FormatFilterStage()
    result = stage.run(_make_items(tmp_files))

    passed_names = {it.file_name for it in result.passed}
    assert "a.docx" in passed_names
    assert "b.pdf" in passed_names
    assert len(result.passed) == 2


def test_disguised_extensions_blocked(tmp_files):
    """扩展名不支持和 magic number 不匹配都应进入异常队列。"""
    stage = FormatFilterStage()
    result = stage.run(_make_items(tmp_files))

    review_names = {it.file_name for it in result.review}
    # 扩展名不支持
    assert "c.txt" in review_names
    # magic number 与扩展名不匹配
    assert "d.docx" in review_names
    assert "e.pdf" in review_names
    assert len(result.review) == 3
