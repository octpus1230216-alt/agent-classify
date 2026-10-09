"""Stage 1：格式筛选（纯代码）。

只接受 .docx / .pdf，并校验文件头 magic number，防止伪装扩展名。
"""

from __future__ import annotations

from pathlib import Path

from pipeline.models import PipelineItem, StageResult
from pipeline.stages.base import BaseStage

# magic number
DOCX_MAGIC = b"PK\x03\x04"
PDF_MAGIC = b"%PDF"
ALLOWED_EXTS = {".docx", ".pdf"}


class FormatFilterStage(BaseStage):
    name = "s1_format_filter"

    def run(self, items: list[PipelineItem]) -> StageResult:
        result = StageResult()
        for item in items:
            path = Path(item.file_path)
            ext = path.suffix.lower()

            if ext not in ALLOWED_EXTS:
                self.mark_review(item, f"不支持的扩展名: {ext}")
                result.review.append(item)
                continue

            if not path.is_file():
                self.mark_review(item, "文件不存在")
                result.review.append(item)
                continue

            if not self._check_magic(path, ext):
                self.mark_review(item, f"文件头与扩展名 {ext} 不匹配（疑似伪装）")
                result.review.append(item)
                continue

            item.status = "passed"
            result.passed.append(item)
        return result

    @staticmethod
    def _check_magic(path: Path, ext: str) -> bool:
        try:
            with open(path, "rb") as f:
                head = f.read(8)
        except OSError:
            return False
        if ext == ".docx":
            return head.startswith(DOCX_MAGIC)
        if ext == ".pdf":
            return head.startswith(PDF_MAGIC)
        return False
