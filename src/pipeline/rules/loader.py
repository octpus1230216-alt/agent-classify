"""YAML 规则加载器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """加载单个 YAML 文件。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"规则文件不存在: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_all_rules(config_dir: str | Path) -> dict[str, dict[str, Any]]:
    """加载 config 目录下的所有规则文件。

    返回结构:
    {
        "config": {...},
        "schema": {...},
        "scoring": {...},
        "grouping": {...},
    }
    """
    base = Path(config_dir)
    return {
        "config": load_yaml(base / "config.yaml"),
        "schema": load_yaml(base / "schema.yaml"),
        "scoring": load_yaml(base / "scoring.yaml"),
        "grouping": load_yaml(base / "grouping.yaml"),
    }
