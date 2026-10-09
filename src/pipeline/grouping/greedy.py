"""阶段 A：高分优先按意向 + 多样性硬约束分配。

确定性算法：同样输入必得到同样输出。
"""

from __future__ import annotations

from typing import Any


def assign_by_preference(
    items: list[Any],
    groups: list[dict],
    max_per_tag: int = 2,
) -> tuple[list[Any], list[Any]]:
    """高分优先按意向分配，硬约束：容量、同标签上限。

    Args:
        items: 需分配的条目，需含 .total_score / .preferences / .tag / .item_id 属性。
               支持通过 .score.total_score 获取分数字段。
        groups: 分组定义，如 [{"id": "g1", "capacity": 30}, ...]。
        max_per_tag: 每组内同标签条目上限。

    Returns:
        (已分配列表, 等待列表)

    确定性保证：按 (-score, item_id) 排序。
    """
    sorted_items = sorted(items, key=lambda x: (-_score(x), x.item_id))

    capacity = {g["id"]: g["capacity"] for g in groups}
    tag_cnt: dict[str, dict[str, int]] = {g["id"]: {} for g in groups}
    waiting: list[Any] = []

    for it in sorted_items:
        assigned = False
        for pref in it.preferences:
            if pref not in capacity:
                continue
            if capacity[pref] <= 0:
                continue
            if tag_cnt[pref].get(it.tag, 0) >= max_per_tag:
                continue
            capacity[pref] -= 1
            tag_cnt[pref][it.tag] = tag_cnt[pref].get(it.tag, 0) + 1
            it.assigned_group = pref
            assigned = True
            break
        if not assigned:
            waiting.append(it)

    return sorted_items, waiting


def _score(item: Any) -> float:
    """从 item 中安全获取分数。"""
    if hasattr(item, "score") and item.score is not None:
        return float(item.score.total_score)
    if hasattr(item, "total_score"):
        return float(item.total_score)
    return 0.0
