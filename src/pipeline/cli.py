"""命令行入口。

Usage:
    python -m pipeline.cli --input data/input --config config
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from pipeline.llm.openai_client import OpenAIClient
from pipeline.orchestrator import Orchestrator
from pipeline.rules.loader import load_all_rules
from pipeline.utils.cache import HashCache


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="doc-pipeline",
        description="批量文档分类处理流水线：格式筛选 -> 必填校验 -> 分类评分 -> 结果登记 -> 分组分配",
    )
    parser.add_argument(
        "--input",
        "-i",
        default=None,
        help="输入目录，默认使用 config 中的 paths.input",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config",
        help="规则配置目录（含 config.yaml / schema.yaml / scoring.yaml / grouping.yaml）",
    )
    args = parser.parse_args()

    load_dotenv()
    rules = load_all_rules(args.config)

    llm_cfg = rules["config"].get("llm", {})
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        llm_client = OpenAIClient(
            model=llm_cfg.get("model", "gpt-4o-mini"),
            temperature=llm_cfg.get("temperature", 0.0),
        )
    else:
        print("[WARN] OPENAI_API_KEY 未设置，Stage 3 将跳过 LLM 调用，所有条目进入人工复核队列")
        llm_client = None

    cache = None
    if llm_cfg.get("cache", True):
        cache_dir = (
            Path(rules["config"]["paths"].get("logs", "data/logs")) / "cache"
        )
        cache = HashCache(cache_dir)

    orch = Orchestrator(rules, llm_client=llm_client, cache=cache)
    result = orch.run(args.input)
    print(
        f"[OK] 通过 {len(result['passed'])} 条, 复核 {len(result['review'])} 条"
    )


if __name__ == "__main__":
    main()
