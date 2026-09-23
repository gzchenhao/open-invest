"""P4-21 — NaturalLanguageFactExtractor（仅抽取用户明确表达的事实）。

LLM 只负责：从 NL 抽取 USER_PROVIDED user facts（REAL 122 契约内）。
LLM 严禁负责：eligibility / benefit / eligible_hired_persons / verification / REAL。

全部 fail-closed：非法 JSON / schema 不符 / 禁止字段 / 类型错误 / provider 不可用 /
空输入 → EXTRACTION_FAILED 或 NO_FACTS_EXTRACTED。绝不猜测、绝不补全。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json

from .contract import ALLOWED_FIELDS, FORBIDDEN_FIELDS, SOURCE_REQUIRED
from .provider import LLMProvider, ProviderUnavailable

EXTRACTION_OK = "ok"
NO_FACTS_EXTRACTED = "NO_FACTS_EXTRACTED"
EXTRACTION_FAILED = "EXTRACTION_FAILED"


class ExtractionRejected(Exception):
    """抽取结果违反契约（禁止字段 / 未知字段 / source 错误 / 类型错误）。"""


@dataclass
class ExtractedFact:
    field: str
    value: Any
    source: str = "user"
    source_text: str = ""
    person_index: Optional[int] = None  # 仅 person 级事实可选：落到第几个人


@dataclass
class ExtractionResult:
    status: str  # EXTRACTION_OK | NO_FACTS_EXTRACTED | EXTRACTION_FAILED
    facts: List[ExtractedFact] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)
    error: Optional[str] = None


class NaturalLanguageFactExtractor:
    """NL -> 严格结构化 user facts（LLM 仅做事实抽取，不做资格/金额判断）。"""

    SYSTEM_PROMPT = (
        "你是从用户自然语言中抽取「用户明确表达的事实」的抽取器。\n"
        "只输出以下允许字段中的事实，且每个 fact 的 source 必须为 \"user\"：\n"
        "- applicant_entity_type（企业/社会组织/个体工商户/...）\n"
        "- hired_persons（整数，总招用人数）\n"
        "- user_stated_eligible_count（整数，用户声称已符合的人数；"
        "注意这不是最终合格人数，不要当作 eligible_hired_persons）\n"
        "- target_group / labor_contract_signed / employment_insurance_paid_months / "
        "hire_date（逐人事实，可带 person_index）\n"
        "严格禁止输出以下字段：eligible_hired_persons、eligibility、benefit、"
        "benefit_amount、verification_status、verified、trust_verified、"
        "government_approved、real_policy_id、approved、policy_truth、amount、rule_type。\n"
        "未明确提供的事实 value 设为 null，不要猜测、不要补全、不要替用户做资格判断。\n"
        "仅返回 JSON，形如："
        "{\"facts\":[{\"field\",\"value\",\"source\",\"source_text\"}],\"unresolved\":[...]}。"
    )

    def __init__(self, provider: LLMProvider):
        self._provider = provider

    def extract(self, nl_text: str) -> ExtractionResult:
        if not nl_text or not str(nl_text).strip():
            return ExtractionResult(NO_FACTS_EXTRACTED, error="empty input")
        # provider 不可用 → fail-closed（绝不 fallback 到 legacy heuristic）
        try:
            raw = self._provider.complete(system=self.SYSTEM_PROMPT, user=nl_text)
        except ProviderUnavailable as e:
            return ExtractionResult(EXTRACTION_FAILED, error=f"provider unavailable: {e}")

        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return ExtractionResult(EXTRACTION_FAILED, error="invalid JSON from provider")

        try:
            facts, unresolved = self._normalize(parsed)
        except ExtractionRejected as e:
            return ExtractionResult(EXTRACTION_FAILED, error=str(e))

        if not facts:
            return ExtractionResult(NO_FACTS_EXTRACTED, facts=[], unresolved=unresolved)
        return ExtractionResult(EXTRACTION_OK, facts=facts, unresolved=unresolved)

    def _normalize(self, parsed: Dict) -> tuple:
        if not isinstance(parsed, dict):
            raise ExtractionRejected("provider 输出不是 JSON 对象")
        flat = parsed.get("facts")
        unresolved = list(parsed.get("unresolved") or [])
        raw_facts: List[Dict] = []
        if isinstance(flat, list):
            raw_facts = flat
        else:
            # 兼容四段式 schema：project_facts / person_facts / aggregate_facts
            for scope in ("project_facts", "person_facts", "aggregate_facts"):
                for f in (parsed.get(scope) or []):
                    raw_facts.append(f)

        facts: List[ExtractedFact] = []
        for f in raw_facts:
            if not isinstance(f, dict):
                raise ExtractionRejected(f"fact 不是对象：{f!r}")
            name = f.get("field")
            if name is None:
                raise ExtractionRejected("fact 缺 field")
            if name in FORBIDDEN_FIELDS:
                raise ExtractionRejected(f"禁止字段进入执行结果：{name}")
            if name not in ALLOWED_FIELDS:
                raise ExtractionRejected(f"字段不在 REAL 122 契约内：{name}")
            source = f.get("source", SOURCE_REQUIRED)
            if source != SOURCE_REQUIRED:
                raise ExtractionRejected(f"fact.source 必须为 user，实际 {source!r}")
            value = self._coerce(name, f.get("value", None))
            facts.append(ExtractedFact(
                field=name, value=value, source="user",
                source_text=str(f.get("source_text", "")),
                person_index=f.get("person_index"),
            ))
        return facts, unresolved

    def _coerce(self, name: str, value: Any) -> Any:
        if value is None:
            return None
        spec = ALLOWED_FIELDS[name]
        t = spec["type"]
        if t is int:
            if isinstance(value, bool):  # bool 是 int 子类，显式拒绝
                raise ExtractionRejected(f"{name} 期望整数，得到布尔")
            if isinstance(value, float) and not value.is_integer():
                raise ExtractionRejected(f"{name} 期望整数，得到 {value!r}")
            try:
                return int(value)
            except (TypeError, ValueError):
                raise ExtractionRejected(f"{name} 期望整数，得到 {value!r}")
        if t is bool:
            if isinstance(value, bool):
                return value
            if value in ("true", "True", True):
                return True
            if value in ("false", "False", False):
                return False
            raise ExtractionRejected(f"{name} 期望布尔，得到 {value!r}")
        if t is str:
            return str(value)
        return value
