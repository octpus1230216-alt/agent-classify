"""文件工具。"""

from __future__ import annotations

from pathlib import Path

from pipeline.models import PipelineItem


def scan_input_dir(input_dir: str | Path) -> list[PipelineItem]:
    """扫描输入目录，生成初始 PipelineItem 列表。

    自动过滤 .gitkeep、隐藏文件、Office 临时文件（~$开头）。
    """
    base = Path(input_dir)
    items: list[PipelineItem] = []
    if not base.exists():
        return items
    for p in sorted(base.iterdir()):
        if not p.is_file():
            continue
        name = p.name
        # 过滤 .gitkeep、隐藏文件、Office 临时文件
        if name == ".gitkeep" or name.startswith(".") or name.startswith("~$"):
            continue
        items.append(PipelineItem(file_path=p, file_name=name))
    return items
