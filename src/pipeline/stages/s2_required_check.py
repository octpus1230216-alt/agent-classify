"""Stage 2：必填项校验（规则为主）。

按 schema.yaml 提取字段，判断必填项缺失、类型/范围是否合法。
明确的空值 / 越界 -> 规则直接判异常；模糊情况才交给 Stage 3。
"""

from __future__ import annotations

from pipeline.models import PipelineItem, StageResult
from pipeline.parsers.docx_parser import parse_docx
from pipeline.parsers.pdf_parser import parse_pdf
from pipeline.rules.validators import validate_fields
from pipeline.stages.base import BaseStage


class RequiredCheckStage(BaseStage):
    name = "s2_required_check"

    def run(self, items: list[PipelineItem]) -> StageResult:
        result = StageResult()
        schema_fields = self.config.get("fields", [])

        for item in items:
            try:
                parsed = self._parse(item)
            except Exception as exc:  # noqa: BLE001
                self.mark_review(item, f"解析失败: {exc}")
                result.review.append(item)
                continue

            # 根据 schema 尝试类型强转
            parsed.fields = _coerce_fields(parsed.fields, schema_fields)

            item.parsed = parsed
            errors = validate_fields(parsed.fields, schema_fields)
            if errors:
                self.mark_review(item, "字段校验失败: " + "; ".join(errors))
                result.review.append(item)
                continue

            item.status = "passed"
            result.passed.append(item)
        return result

    @staticmethod
    def _parse(item: PipelineItem):
        ext = item.file_path.suffix.lower()
        if ext == ".docx":
            return parse_docx(item.file_path)
        if ext == ".pdf":
            return parse_pdf(item.file_path)
        raise ValueError(f"不支持的格式: {ext}")


def _coerce_fields(fields: dict, schema_fields: list[dict]) -> dict:
    """根据 schema 的 type 对 fields 尝试类型强转。

    解析器提取的字段默认都是字符串，这里做尽量保守的转换：
    - string "85" -> number 85.0
    - string "a, b" -> list[string] ["a", "b"]
    转换失败则保留原值，交给后续 validate_fields 报错。
    """
    result = dict(fields)
    schema_map = {f["name"]: f for f in schema_fields}

    for name, value in result.items():
        rule = schema_map.get(name)
        if not rule:
            continue
        ftype = rule.get("type", "string")

        if ftype == "number" and isinstance(value, str):
            try:
                result[name] = float(value.strip())
            except ValueError:
                pass  # 保留字符串，后续校验会报错

        elif ftype == "list[string]" and isinstance(value, str):
            # 尝试逗号分隔
            result[name] = [s.strip() for s in value.split(",") if s.strip()]

    return result
