"""Prompt 模板：要求模型返回严格 JSON。"""

from __future__ import annotations

import json
from typing import Any


def build_classify_prompt(content: str, scoring_config: dict[str, Any]) -> str:
    """根据 scoring.yaml 动态构造 Prompt。

    要求模型必须返回严格 JSON（配合 response_format=json_object 强制）。
    """
    categories = scoring_config.get("categories", [])
    dimensions = scoring_config.get("dimensions", [])
    total = scoring_config.get("total", 100)

    dim_desc = "\n".join(
        f"- {d['id']} (权重 {d['weight']}, 满分 {d['max_score']}): {d['desc']}"
        for d in dimensions
    )

    schema = {
        "category": f"必须属于 {categories} 之一",
        "field_scores": "{维度id: 分数}",
        "total_score": f"0-{total}",
        "reason": "简要说明",
        "need_human": "true/false，不确定时为 true",
    }

    return (
        "你是一个文档分类与评分助手。请根据以下内容完成分类和评分。\n\n"
        f"可选分类: {categories}\n\n"
        f"评分维度:\n{dim_desc}\n\n"
        f"总分上限: {total}\n\n"
        "请严格返回 JSON，格式如下（不要包含其他文字）:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
        "待处理内容:\n"
        f"{content}\n"
    )
