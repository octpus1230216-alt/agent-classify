"""LLM 调用缓存：相同内容不重复调用。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class HashCache:
    """基于文件的 JSON 缓存。

    以 SHA-256 作为 key，缓存 value 为 dict（JSON 可序列化）。
    """

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        if key in self._mem:
            return self._mem[key]
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self._mem[key] = data
            return data
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._mem[key] = value
        path = self.cache_dir / f"{key}.json"
        path.write_text(
            json.dumps(value, ensure_ascii=False), encoding="utf-8"
        )
