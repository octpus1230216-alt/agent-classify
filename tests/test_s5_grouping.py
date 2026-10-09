"""Stage 5 分组测试：高分优先、同标签<=N、容量不超、确定性。"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.grouping.greedy import assign_by_preference


@dataclass
class FakeScore:
    total_score: float


@dataclass
class FakeItem:
    """测试用假条目，实现 assign_by_preference 所需接口。"""

    item_id: str
    total_score: float
    preferences: list[str]
    tag: str
    assigned_group: str | None = None

    @property
    def score(self):
        return FakeScore(self.total_score)


def _build_items() -> list[FakeItem]:
    return [
        FakeItem("i1", 90, ["g1", "g2"], "tag_a"),
        FakeItem("i2", 80, ["g1"], "tag_a"),
        FakeItem("i3", 70, ["g1"], "tag_a"),  # 同 tag_a 在 g1 已满 2 -> 进入 waiting
        FakeItem("i4", 60, ["g2"], "tag_b"),
        FakeItem("i5", 50, ["g1"], "tag_c"),
    ]


def test_high_score_first_and_tag_constraint():
    """高分优先分配 + 同标签 <=N 硬约束。"""
    items = _build_items()
    groups = [{"id": "g1", "capacity": 3}, {"id": "g2", "capacity": 3}]
    assigned, waiting = assign_by_preference(items, groups, max_per_tag=2)

    assigned_map = {it.item_id: it.assigned_group for it in assigned}
    # i1/i2 都是 tag_a -> g1 先装 2 个
    assert assigned_map["i1"] == "g1"
    assert assigned_map["i2"] == "g1"
    # i3 也是 tag_a，g1 同标签已满 -> 进入 waiting
    assert "i3" in [it.item_id for it in waiting]
    # i4 tag_b -> 意向 g2 可行
    assert assigned_map["i4"] == "g2"
    # i5 tag_c -> 意向 g1 可行（同标签约束仅限制 tag_c<=1）
    assert assigned_map["i5"] == "g1"


def test_capacity_not_exceeded():
    """各组容量不得超出。"""
    items = _build_items()
    groups = [{"id": "g1", "capacity": 1}, {"id": "g2", "capacity": 1}]
    assigned, _ = assign_by_preference(items, groups, max_per_tag=2)

    g1_count = sum(1 for it in assigned if it.assigned_group == "g1")
    g2_count = sum(1 for it in assigned if it.assigned_group == "g2")
    assert g1_count <= 1
    assert g2_count <= 1


def test_deterministic_same_input():
    """同样输入两次应得到完全相同的分组结果。"""
    groups = [{"id": "g1", "capacity": 3}, {"id": "g2", "capacity": 3}]

    def run() -> dict[str, str | None]:
        items = _build_items()
        assigned, _ = assign_by_preference(items, groups, max_per_tag=2)
        return {it.item_id: it.assigned_group for it in assigned}

    assert run() == run(), "分组结果必须确定性一致"


def test_ignores_nonexistent_preferences():
    """意向上不在 groups 中的组应被跳过。"""
    items = [FakeItem("i1", 90, ["nonexistent", "g1"], "tag_a")]
    groups = [{"id": "g1", "capacity": 1}]
    assigned, waiting = assign_by_preference(items, groups, max_per_tag=2)
    assert assigned[0].assigned_group == "g1"
    assert waiting == []
