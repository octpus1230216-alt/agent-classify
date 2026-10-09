"""OpenAI 兼容接口实现（支持 Qwen / DeepSeek 等兼容服务）。"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from pipeline.llm.base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """通过 OpenAI 兼容协议调用任何支持 JSON mode 的大模型。

    切换模型只需修改 config.yaml 的 llm.model 和 .env 的 OPENAI_BASE_URL。
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        self.model = model
        self.temperature = temperature
        # 允许 api_key 为 None（延迟到 chat_json 再报错）
        # 这样 Stage 3 会捕获异常并标记 review，不影响 S1/S2/S4/S5
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY") or "",
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )

    def chat_json(self, prompt: str) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
