"""Stage 3 分类评分测试：mock 模型，验证 JSON 解析与阈值路由。"""

from __future__ import annotations

from pathlib import Path

from pipeline.llm.base import BaseLLMClient
from pipeline.models import ParsedDocument, PipelineItem
from pipeline.stages.s3_classify_score import ClassifyScoreStage
from pipeline.utils.cache import HashCache


class MockLLM(BaseLLMClient):
    """可预设响应的 Mock 大模型。"""

    def __init__(self, response: dict):
        self._response = response
        self.calls = 0

    def chat_json(self, prompt: str) -> dict:
        self.calls += 1
        return self._response


def _make_item(text: str = "sample content") -> PipelineItem:
    item = PipelineItem(file_path=Path("a.docx"), file_name="a.docx")
    item.parsed = ParsedDocument(
        file_path=Path("a.docx"), raw_text=text, fields={"item_id": "i1"}
    )
    return item


SCORING_CONFIG = {
    "categories": ["type_a", "type_b", "type_c"],
    "dimensions": [
        {"id": "dim_a", "weight": 0.4, "max_score": 40, "desc": "a"},
        {"id": "dim_b", "weight": 0.6, "max_score": 60, "desc": "b"},
    ],
    "total": 100,
    "need_human_threshold": 60,
}


def test_above_threshold_passes():
    """高于阈值且 need_human=false -> 通过。"""
    mock = MockLLM({
        "category": "type_a",
        "field_scores": {"dim_a": 32, "dim_b": 50},
        "total_score": 82,
        "reason": "ok",
        "need_human": False,
    })
    stage = ClassifyScoreStage(SCORING_CONFIG, llm_client=mock)
    result = stage.run([_make_item()])

    assert len(result.passed) == 1
    assert result.passed[0].score.total_score == 82
    assert result.passed[0].score.category == "type_a"


def test_below_threshold_to_review():
    """低于阈值 -> 人工复核。"""
    mock = MockLLM({
        "category": "type_b",
        "field_scores": {"dim_a": 10, "dim_b": 20},
        "total_score": 30,
        "reason": "low",
        "need_human": False,
    })
    stage = ClassifyScoreStage(SCORING_CONFIG, llm_client=mock)
    result = stage.run([_make_item()])

    assert len(result.review) == 1
    assert "需人工复核" in result.review[0].review_reason


def test_need_human_flag_to_review():
    """need_human=true 强制人工复核。"""
    mock = MockLLM({
        "category": "type_c",
        "field_scores": {"dim_a": 40, "dim_b": 60},
        "total_score": 100,
        "reason": "uncertain",
        "need_human": True,
    })
    stage = ClassifyScoreStage(SCORING_CONFIG, llm_client=mock)
    result = stage.run([_make_item()])

    assert len(result.review) == 1


def test_cache_avoids_duplicate_call(tmp_path):
    """相同内容应命中缓存，模型只被调用一次。"""
    mock = MockLLM({
        "category": "type_a",
        "field_scores": {"dim_a": 32, "dim_b": 50},
        "total_score": 82,
        "reason": "ok",
        "need_human": False,
    })
    cache = HashCache(tmp_path / "cache")
    stage = ClassifyScoreStage(SCORING_CONFIG, llm_client=mock, cache=cache)

    item1 = _make_item("same text")
    item2 = _make_item("same text")
    stage.run([item1, item2])

    assert mock.calls == 1, "相同内容应命中缓存，LLM 仅调用一次"
