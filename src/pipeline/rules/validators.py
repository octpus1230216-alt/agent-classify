"""字段校验器：按 schema 检查必填、类型、范围。"""

from __future__ import annotations

from typing import Any


def validate_fields(fields: dict[str, Any], schema_fields: list[dict]) -> list[str]:
    """校验字段是否符合 schema 定义。

    返回错误信息列表；空列表表示通过。
    """
    errors: list[str] = []
    schema_map = {f["name"]: f for f in schema_fields}

    for name, rule in schema_map.items():
        value = fields.get(name)

        if rule.get("required", False):
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append(f"必填字段缺失: {name}")
                continue

        if value is None:
            continue

        ftype = rule.get("type", "string")
        if not _check_type(value, ftype):
            errors.append(f"字段 {name} 类型错误，期望 {ftype}")
            continue

        if ftype == "number" and "valid_range" in rule:
            lo, hi = rule["valid_range"]
            if not (lo <= float(value) <= hi):
                errors.append(f"字段 {name} 越界，期望 [{lo}, {hi}]")

    return errors


def _check_type(value: Any, ftype: str) -> bool:
    """检查值是否符合目标类型。"""
    if ftype == "string":
        return isinstance(value, str)
    if ftype == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if ftype == "list[string]":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    return True
