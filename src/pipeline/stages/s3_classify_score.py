"""Stage 3：内容分类与评分（唯一使用大模型的环节）。

从 scoring.yaml 读取分类类别、评分维度、权重、满分、阈值。
低于阈值或 need_human=true -> 异常队列。
"""

from __future__ import annotations

from typing import Any

from pipeline.llm.base import BaseLLMClient
from pipeline.llm.prompt_templates import build_classify_prompt
from pipeline.models import PipelineItem, ScoredItem, StageResult
from pipeline.stages.base import BaseStage
from pipeline.utils.cache import HashCache


class ClassifyScoreStage(BaseStage):
    name = "s3_classify_score"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        llm_client: BaseLLMClient | None = None,
        cache: HashCache | None = None,
    ) -> None:
        super().__init__(config)
        self.llm = llm_client
        self.cache = cache
        self.threshold = self.config.get("need_human_threshold", 60)

    def run(self, items: list[PipelineItem]) -> StageResult:
        result = StageResult()
        for item in items:
            scored = self._classify(item)
            if scored is None:
                self.mark_review(item, "分类评分失败")
                result.review.append(item)
                continue

            item.score = scored
            if scored.need_human or scored.total_score < self.threshold:
                self.mark_review(
                    item,
                    f"需人工复核: need_human={scored.need_human}, "
                    f"score={scored.total_score}<{self.threshold}",
                )
                result.review.append(item)
                continue

            item.status = "passed"
            result.passed.append(item)
        return result

    def _classify(self, item: PipelineItem) -> ScoredItem | None:
        if not self.llm or not item.parsed:
            return None

        content = item.parsed.raw_text
        cache_key = self._cache_key(content)

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return self._to_scored(cached, item)

        prompt = build_classify_prompt(content, self.config)
        try:
            raw = self.llm.chat_json(prompt)
        except Exception:  # noqa: BLE001
            return None

        if self.cache:
            self.cache.set(cache_key, raw)
        return self._to_scored(raw, item)

    @staticmethod
    def _cache_key(content: str) -> str:
        import hashlib
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _to_scored(raw: dict[str, Any], item: PipelineItem) -> ScoredItem:
        return ScoredItem(
            item_id=item.item_id,
            category=str(raw.get("category", "")),
            field_scores={k: float(v) for k, v in raw.get("field_scores", {}).items()},
            total_score=float(raw.get("total_score", 0)),
            reason=str(raw.get("reason", "")),
            need_human=bool(raw.get("need_human", False)),
            raw_response=raw,
        )
