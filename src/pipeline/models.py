"""流水线通用数据模型。

所有 Stage 共享同一套数据结构，保证接口统一、可替换。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ParsedDocument:
    """Stage 2 解析后的文档对象。"""

    file_path: Path
    raw_text: str
    fields: dict[str, Any] = field(default_factory=dict)
    tables: list[list[list[str]]] = field(default_factory=list)


@dataclass
class ScoredItem:
    """Stage 3 评分后的条目。"""

    item_id: str
    category: str
    field_scores: dict[str, float]
    total_score: float
    reason: str = ""
    need_human: bool = False
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineItem:
    """贯穿流水线的单条记录。"""

    file_path: Path
    file_name: str
    parsed: Optional[ParsedDocument] = None
    score: Optional[ScoredItem] = None
    assigned_group: Optional[str] = None
    status: str = "pending"  # pending | passed | review
    review_reason: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def item_id(self) -> str:
        if self.parsed and self.parsed.fields.get("item_id"):
            return str(self.parsed.fields["item_id"])
        return self.file_name

    @property
    def tag(self) -> str:
        return str(self.parsed.fields.get("tag", "")) if self.parsed else ""

    @property
    def preferences(self) -> list[str]:
        if not self.parsed:
            return []
        prefs = self.parsed.fields.get("preferences", [])
        return [str(p) for p in prefs] if isinstance(prefs, list) else []


@dataclass
class StageResult:
    """每个 Stage 的统一输出：通过项 + 异常项。"""

    passed: list[PipelineItem] = field(default_factory=list)
    review: list[PipelineItem] = field(default_factory=list)
