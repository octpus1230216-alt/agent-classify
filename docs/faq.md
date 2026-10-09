# 常见问题

## 如何切换大模型？

修改 `config/config.yaml` 的 `llm.model`，并在 `.env` 中设置对应 `OPENAI_BASE_URL`：

| 提供商 | OPENAI_BASE_URL |
|--------|----------------|
| OpenAI | `https://api.openai.com/v1` |
| Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| DeepSeek | `https://api.deepseek.com` |

所有兼容 OpenAI 协议的服务均可直接使用 `OpenAIClient`。

## 为什么分组不用大模型？

分组是带硬约束（容量、同标签上限）的分配问题，大模型无法保证约束满足与结果确定性。本项目用贪心算法实现，可复现、可测试。如需更优解，可升级为 OR-Tools CP-SAT（`grouping/adjust.py` 已预留注释说明）。

## 如何新增一个 Stage？

1. 在 `src/pipeline/stages/` 下继承 `BaseStage`，实现 `run()`。
2. 在 `orchestrator.py` 中按顺序插入调用。
3. 异常项统一 `mark_review()` 并加入 `StageResult.review`。

## 真实规则会被提交到 Git 吗？

不会。`.gitignore` 已排除 `config/*.yaml`、`data/`、`.env`、`*.docx/pdf/xlsx`。仓库仅含脱敏示例。

## Stage 2 字段提取如何定制？

目前为占位键值解析（仅识别 `key: value` 形式）。请根据实际模板结构修改 `parsers/docx_parser.py` 和 `parsers/pdf_parser.py` 中的 `_extract_fields` 函数。

## 为什么 S4 放在 S5 之后？

因为 S5 分组后 `assigned_group` 才被写入 `PipelineItem`。先分组再登记，让 `result.xlsx` 包含完整的分组信息。
