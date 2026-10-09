"""Stage 抽象基类，统一接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pipeline.models import PipelineItem, StageResult


class BaseStage(ABC):
    """所有 Stage 的统一接口。"""

    name: str = "base"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def run(self, items: list[PipelineItem]) -> StageResult:
        """执行 Stage，返回通过项与异常项。"""
        raise NotImplementedError

    def mark_review(self, item: PipelineItem, reason: str) -> None:
        item.status = "review"
        item.review_reason = reason
