# 规则配置目录

本目录存放流水线的所有规则定义。**真实规则文件（`*.yaml`）不入库**，仓库仅提供脱敏示例 `*.example.yaml`。

## 使用方式

1. 将 `*.example.yaml` 复制为同名 `*.yaml`（去掉 `.example`）：
   ```bash
   cp config.example.yaml config.yaml
   cp schema.example.yaml schema.yaml
   cp scoring.example.yaml scoring.yaml
   cp grouping.example.yaml grouping.yaml
   ```
2. 按实际业务填充字段、分类、评分维度、分组等规则。
3. `.gitignore` 已排除 `config/*.yaml`，真实规则不会被提交。

## 文件说明

| 文件 | 作用 |
|------|------|
| `config.yaml` | 全局运行参数（LLM、路径、流水线开关） |
| `schema.yaml` | 字段定义、必填项、类型与取值范围 |
| `scoring.yaml` | 分类类别、评分维度、权重、阈值 |
| `grouping.yaml` | 分组容量、同标签上限、再分配规则 |

规则字段格式详见 [`docs/rule-format.md`](../docs/rule-format.md)。
