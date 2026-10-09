"""日志工具。"""

from __future__ import annotations

import logging
from pathlib import Path


def get_logger(
    name: str = "pipeline", log_dir: str | Path | None = None
) -> logging.Logger:
    """获取带控制台 + 文件输出的 Logger。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(
            Path(log_dir) / "pipeline.log", encoding="utf-8"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
