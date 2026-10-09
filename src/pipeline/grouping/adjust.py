"""阶段 B：剩余项贪心再分配。

预留 OR-Tools 接口（注释说明可升级），但不强依赖。
硬约束：每组容量、同标签<=N；软约束：尽量贴近意向、组间均衡。
"""

from __future__ import annotations

from typing import Any


def adjust_remaining(
    waiting: list[Any],
    groups: list[dict],
    max_per_tag: int,
    rules: list[dict] | None = None,
) -> list[Any]:
    """对阶段 A 未分配的条目做贪心再分配。

    策略：
    1. nearest_preference：按意向顺序找第一个可容纳的组。
    2. balance_size：在意向不可行时，选当前容量最大的组（即人数最少）。

    仍无法分配的条目进入最终等待列表。

    NOTE: 可升级为 OR-Tools CP-SAT 求解器，以组间均衡为目标函数，
    容量与同标签上限为硬约束。此处保留纯贪心实现，不引入强依赖。
    升级示意:
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()
        # x[i][g] = 1 表示 item i 分到 group g
        # 硬约束: sum_i x[i][g] <= capacity[g]
        #        sum_{i: tag==t} x[i][g] <= max_per_tag
        # 软目标: min |capacity[g] - sum_i x[i][g]|  (组间均衡)
    """
    rules = rules or []
    rule_types = [r.get("type") for r in rules]

    capacity = {g["id"]: g["capacity"] for g in groups}
    tag_cnt: dict[str, dict[str, int]] = {g["id"]: {} for g in groups}

    remaining: list[Any] = []
    for it in waiting:
        target = _pick_group(it, capacity, tag_cnt, max_per_tag, rule_types)
        if target is not None:
            capacity[target] -= 1
            tag_cnt[target][it.tag] = tag_cnt[target].get(it.tag, 0) + 1
            it.assigned_group = target
        else:
            remaining.append(it)
    return remaining


def _pick_group(
    item: Any,
    capacity: dict[str, int],
    tag_cnt: dict[str, dict[str, int]],
    max_per_tag: int,
    rule_types: list[str],
) -> str | None:
    """根据规则选一个可行组。"""
    feasible = [
        gid
        for gid, cap in capacity.items()
        if cap > 0 and tag_cnt[gid].get(item.tag, 0) < max_per_tag
    ]
    if not feasible:
        return None

    if "nearest_preference" in rule_types:
        for pref in item.preferences:
            if pref in feasible:
                return pref

    if "balance_size" in rule_types:
        # 选剩余容量最大的组（即当前人数最少）
        return max(feasible, key=lambda g: capacity[g])

    return feasible[0]
