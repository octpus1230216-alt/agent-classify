"""Stage 5：分组分配（纯算法）。

阶段 A：高分优先按意向 + 多样性硬约束。
阶段 B：剩余项按 grouping.yaml 规则再分配（贪心）。
"""

from __future__ import annotations

from pipeline.grouping.adjust import adjust_remaining
from pipeline.grouping.greedy import assign_by_preference
from pipeline.models import PipelineItem, StageResult
from pipeline.stages.base import BaseStage


class GroupingStage(BaseStage):
    name = "s5_grouping"

    def run(self, items: list[PipelineItem]) -> StageResult:
        result = StageResult()
        groups = self.config.get("groups", [])
        max_per_tag = self.config.get("constraints", {}).get("max_per_tag", 2)

        # 阶段 A：高分优先按意向分配
        assigned, waiting = assign_by_preference(
            items, groups, max_per_tag=max_per_tag
        )

        # 阶段 B：剩余项贪心再分配
        adjust_rules = self.config.get("adjustment_rules", [])
        final_waiting = adjust_remaining(waiting, groups, max_per_tag, adjust_rules)

        for it in assigned:
            it.status = "passed"
            result.passed.append(it)
        for it in final_waiting:
            self.mark_review(it, "无法分配到任何组（容量/标签约束）")
            result.review.append(it)
        return result
