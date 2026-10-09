"""流水线编排器：按顺序调用 S1 -> S5，收集异常队列。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook

from pipeline.models import PipelineItem
from pipeline.stages.s1_format_filter import FormatFilterStage
from pipeline.stages.s2_required_check import RequiredCheckStage
from pipeline.stages.s3_classify_score import ClassifyScoreStage
from pipeline.stages.s4_register import RegisterStage
from pipeline.stages.s5_grouping import GroupingStage
from pipeline.utils.file_utils import scan_input_dir
from pipeline.utils.logger import get_logger


class Orchestrator:
    """串行编排 S1->S2->S3->S5->S4。

    S4 放在 S5 之后，让 result.xlsx 含分组结果。
    """

    def __init__(self, rules: dict[str, dict[str, Any]], llm_client=None, cache=None) -> None:
        self.rules = rules
        cfg = rules["config"]
        self.paths = cfg.get("paths", {})
        self.logger = get_logger(log_dir=self.paths.get("logs"))

        self.s1 = FormatFilterStage()
        self.s2 = RequiredCheckStage(rules["schema"])
        self.s3 = ClassifyScoreStage(rules["scoring"], llm_client=llm_client, cache=cache)
        self.s5 = GroupingStage(rules["grouping"])
        self.s4 = RegisterStage(
            {
                "output_dir": self.paths.get("output"),
                "logs_dir": self.paths.get("logs"),
                "flush_every": cfg.get("pipeline", {}).get("flush_every", 10),
            }
        )

    def run(
        self, input_dir: str | Path | None = None
    ) -> dict[str, list[PipelineItem]]:
        """执行完整流水线，返回通过项 + 异常项。"""
        input_dir = input_dir or self.paths.get("input", "data/input")
        items = scan_input_dir(input_dir)
        self.logger.info("扫描到 %d 个文件", len(items))

        all_review: list[PipelineItem] = []

        # S1 格式筛选
        r1 = self.s1.run(items)
        all_review.extend(r1.review)
        self.logger.info("S1 通过 %d, 异常 %d", len(r1.passed), len(r1.review))

        # S2 必填项校验
        r2 = self.s2.run(r1.passed)
        all_review.extend(r2.review)
        self.logger.info("S2 通过 %d, 异常 %d", len(r2.passed), len(r2.review))

        # S3 分类评分（LLM）
        r3 = self.s3.run(r2.passed)
        all_review.extend(r3.review)
        self.logger.info("S3 通过 %d, 异常 %d", len(r3.passed), len(r3.review))

        # S5 分组分配（纯算法）
        r5 = self.s5.run(r3.passed)
        all_review.extend(r5.review)
        self.logger.info("S5 通过 %d, 异常 %d", len(r5.passed), len(r5.review))

        # S4 结果登记（放在最后，让 result.xlsx 含分组结果）
        all_items = r5.passed + all_review
        self.s4.run(all_items)

        # 写人工复核队列
        self._write_review_queue(all_review)
        self.logger.info(
            "流水线完成：通过 %d 条，复核 %d 条", len(r5.passed), len(all_review)
        )
        return {"passed": r5.passed, "review": all_review}

    def _write_review_queue(self, review_items: list[PipelineItem]) -> None:
        """将异常项写入 data/review/review_queue.xlsx。"""
        review_dir = Path(self.paths.get("review", "data/review"))
        review_dir.mkdir(parents=True, exist_ok=True)
        if not review_items:
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "review_queue"
        headers = ["item_id", "file_name", "status", "review_reason"]
        ws.append(headers)
        for it in review_items:
            ws.append([it.item_id, it.file_name, it.status, it.review_reason])
        wb.save(review_dir / "review_queue.xlsx")
