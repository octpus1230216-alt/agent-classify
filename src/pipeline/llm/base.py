"""大模型抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    """统一的大模型调用接口，支持 OpenAI / Qwen / DeepSeek 替换。"""

    @abstractmethod
    def chat_json(self, prompt: str) -> dict[str, Any]:
        """发送 prompt，返回严格 JSON 解析后的 dict。"""
        raise NotImplementedError
