# 规则文件格式

所有规则文件均为 YAML 格式，位于 `config/` 目录。仓库仅含 `*.example.yaml`，使用时复制为 `*.yaml`。

## config.yaml — 全局运行参数

```yaml
llm:
  provider: openai            # openai | qwen | deepseek
  model: gpt-4o-mini
  temperature: 0.0
  cache: true
  max_retries: 2

paths:
  input: data/input
  output: data/output
  review: data/review
  logs: data/logs

pipeline:
  flush_every: 10             # Stage4 每 N 条落盘一次
  review_output: review_queue.xlsx
```

## schema.yaml — 字段定义

```yaml
fields:
  - name: item_id              # 字段名（程序内标识）
    label: "编号"              # 显示名
    required: true             # 是否必填
    type: string               # string | number | list[string]
    valid_range: [0, 100]      # 仅 number 类型可用
```

## scoring.yaml — 分类与评分

```yaml
categories:                    # 可选分类列表
  - type_a
  - type_b

dimensions:                    # 评分维度
  - id: dim_a
    desc: "维度说明"
    weight: 0.4                # 权重（所有权重之和应为 1.0）
    max_score: 40              # 该维度满分

total: 100                     # 总分上限
need_human_threshold: 60       # 低于此分进入人工复核
```

## grouping.yaml — 分组分配

```yaml
groups:
  - id: group_1
    capacity: 30               # 组容量

constraints:
  max_per_tag: 2               # 每组内同标签条目上限

adjustment_rules:              # 阶段 B 再分配策略
  - type: nearest_preference   # 优先贴近意向
  - type: balance_size         # 组间均衡（选容量最大的空闲组）
```
