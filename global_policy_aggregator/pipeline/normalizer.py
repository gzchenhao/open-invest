"""P3-2 Normalizer — ParsedContent → Candidate。

逐字段 null-safe 抽取。纪律：宁可 null，不要猜；每个非 null 内容抽取字段必须带
verbatim quote evidence。复用的纯逻辑：canonical_taxonomy.get_registry().resolve()
（industry 映射）；金额/日期的正则抽取为独立纯函数，仅在有明确证据时填充。
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional, Tuple

from schema.canonical_taxonomy import get_registry

from global_policy_aggregator.pipeline.candidate import (
    Candidate,
    FieldEvidence,
    Provenance,
)
from global_policy_aggregator.pipeline.parser import (
    ParsedContent,
    ParseError,
    ParseFailure,
    parse_html,
    record_parse_failure,
)

# ── 常量 ────────────────────────────────────────────────────────────────
POLICY_TYPE_VOCAB = {
    "plan", "opinion", "measure", "notice", "subsidy", "tax_break", "other", "unknown",
}

# type 受控词表映射（仅当页面显式类型证据出现才映射）
TYPE_LABEL_MAP = [
    ("规划", "plan"),
    ("意见", "opinion"),
    ("办法", "measure"),
    ("通知", "notice"),
    ("补贴", "subsidy"),
    ("税收优惠", "tax_break"),
    ("税收", "tax_break"),
    ("减免税", "tax_break"),
]

# industry 抽取所需的「产业意图」邻近词（比普通关键词匹配更严格）
INDUSTRY_INTENT_WORDS = [
    "产业", "企业", "领域", "支持", "面向", "鼓励", "专项",
    "方向", "聚焦", "重点", "从事", "主营", "培育", "扶持",
]

# amount 禁止推断的语义标记
AMOUNT_FORBIDDEN_TOKENS = ["%", "比例", "按投资", "原则上", "适当支持", "原则上给予", "据实"]

UNIT_MULTIPLIER = {
    "万元": 10_000, "万": 10_000,
    "亿元": 100_000_000, "亿": 100_000_000,
    "元": 1,
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _candidate_id(source_url: str, clean_text: str) -> str:
    h = hashlib.sha1((source_url + "|" + clean_text[:200]).encode("utf-8")).hexdigest()
    return "cand_" + h[:12]


def _span_of(clean_text: str, quote: str) -> Optional[Tuple[int, int]]:
    idx = clean_text.find(quote)
    if idx < 0:
        return None
    return (idx, idx + len(quote))


def _window(text: str, start: int, end: int, pad: int = 40) -> str:
    s = max(0, start - pad)
    e = min(len(text), end + pad)
    return text[s:e].strip()


def _norm_date(s: str) -> Optional[str]:
    """将中文/ISO 日期归一为 YYYY-MM-DD。"""
    m = re.match(r"((?:19|20)\d{2})年(\d{1,2})月(\d{1,2})日", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


# ── 逐字段抽取器 ────────────────────────────────────────────────────────
def extract_title(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    candidates = []
    if parsed.h1_raw:
        candidates.append(parsed.h1_raw)
    m = re.search(r"《([^》]+)》", parsed.clean_text)
    if m:
        candidates.append(m.group(1))
    if parsed.title_raw:
        candidates.append(parsed.title_raw)
    # 优先级：h1 / 《》 / title tag；取首个非空候选，避免多候选时硬猜
    for cand in candidates:
        cand = cand.strip()
        if cand:
            return FieldEvidence(
                field_name="title", value=cand, quote=cand,
                snapshot_ref=snapshot_ref,
                char_span=_span_of(parsed.clean_text, cand),
                extracted_at=_utcnow(), method="bs4_title_or_booktitle",
            )
    return FieldEvidence(field_name="title", value=None,
                         null_reason="no_explicit_title_found", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_source_url(source_url: str, snapshot_ref: Optional[str]) -> FieldEvidence:
    # 来自 P3-1 fetch，非网页内容推断
    return FieldEvidence(
        field_name="source_url", value=source_url, quote=source_url,
        snapshot_ref=snapshot_ref, method="passthrough_from_fetch",
        extracted_at=_utcnow(),
    )


def extract_description(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    # 仅截取正文原文前段，绝不摘要改写
    snippet = parsed.clean_text[:400].strip()
    if not snippet:
        return FieldEvidence(field_name="description", value=None,
                             null_reason="no_substantive_body", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    return FieldEvidence(
        field_name="description", value=snippet, quote=snippet,
        snapshot_ref=snapshot_ref, char_span=(0, len(snippet)),
        extracted_at=_utcnow(), method="verbatim_slice",
    )


def extract_source_organization(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    patterns = [
        r"(发布机关|发布单位|发文机关|制定机关|发布部门)[:：]\s*([\u4e00-\u9fa5A-Za-z（）()·0-9]+)",
        r"([\u4e00-\u9fa5]{2,20}?(?:部|委员会|局|厅|办公厅|署))\s*(?:关于印发|发布|颁布)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            org = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
            org = org.strip()
            if org:
                return FieldEvidence(
                    field_name="source_organization", value=org, quote=m.group(0).strip(),
                    snapshot_ref=snapshot_ref, char_span=_span_of(text, m.group(0).strip()),
                    extracted_at=_utcnow(), method="regex_publisher_label",
                )
    return FieldEvidence(field_name="source_organization", value=None,
                         null_reason="no_explicit_publisher", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_region(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    # 1) 显式地区标签
    m = re.search(
        r"(?:地区|区域|所在地|适用地区|执行地区|所在地区)[:：]\s*"
        r"([\u4e00-\u9fa5]{2,12}(?:省|市|自治区|特别行政区))", text)
    if m:
        region = m.group(1).strip()
        return FieldEvidence(field_name="region", value=region, quote=m.group(0).strip(),
                             snapshot_ref=snapshot_ref,
                             char_span=_span_of(text, m.group(0).strip()),
                             extracted_at=_utcnow(), method="regex_region_label")
    # 2) 标题/正文开头出现的明确行政区划（不做层级推断）
    search_scope = (parsed.title_raw or "") + "\n" + (parsed.h1_raw or "") + "\n" + text[:200]
    m2 = re.search(r"([\u4e00-\u9fa5]{2,10}(?:省|市|自治区|特别行政区))", search_scope)
    if m2:
        region = m2.group(1).strip()
        return FieldEvidence(field_name="region", value=region, quote=region,
                             snapshot_ref=snapshot_ref,
                             char_span=_span_of(text, region),
                             extracted_at=_utcnow(), method="regex_admin_division")
    return FieldEvidence(field_name="region", value=None,
                         null_reason="no_explicit_region", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_type(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    # 仅在标题/H1 中识别政策类型（明确的文件类型证据），不扫描正文避免误判。
    scope = (parsed.title_raw or "") + "\n" + (parsed.h1_raw or "")
    for label, vocab in TYPE_LABEL_MAP:
        if label in scope:
            return FieldEvidence(field_name="type", value=vocab, quote=label,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(parsed.clean_text, label) or _span_of(scope, label),
                                 extracted_at=_utcnow(), method="regex_type_label")
    return FieldEvidence(field_name="type", value="unknown",
                         null_reason="no_reliable_type_evidence", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_issue_date(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    m = re.search(
        r"(发布日期|发布时间|成文日期|印发日期|发文日期|发布)[:：]\s*"
        r"((?:19|20)\d{2}年\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
    if m:
        iso = _norm_date(m.group(2))
        if iso:
            return FieldEvidence(field_name="issue_date", value=iso, quote=m.group(0).strip(),
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, m.group(0).strip()),
                                 extracted_at=_utcnow(), method="regex_issue_date")
    return FieldEvidence(field_name="issue_date", value=None,
                         null_reason="no_explicit_issue_date", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_valid_period(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    m = re.search(
        r"((?:19|20)\d{2}年\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})"
        r"\s*(?:至|—|~|到|起至|止)\s*"
        r"((?:19|20)\d{2}年\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
    if m:
        start = _norm_date(m.group(1))
        end = _norm_date(m.group(2))
        if start and end:
            return FieldEvidence(
                field_name="valid_period", value={"start": start, "end": end},
                quote=m.group(0).strip(), snapshot_ref=snapshot_ref,
                char_span=_span_of(text, m.group(0).strip()),
                extracted_at=_utcnow(), method="regex_valid_period",
            )
    # 只有开始日期或完全无 → null（禁止默认 end_date）
    return FieldEvidence(field_name="valid_period", value=None,
                         null_reason="no_explicit_valid_period_both_dates", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_industry(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """严格 industry 抽取：仅当产业词出现在产业意图语境中才映射 canonical taxonomy。"""
    text = parsed.clean_text
    registry = get_registry()
    keyword_map = []
    for ind in registry.list():
        for alias in ind.aliases:
            if alias:
                keyword_map.append((alias, ind.id))
        keyword_map.append((ind.id, ind.id))

    best = None  # (canonical_id, quote)
    for kw, cid in keyword_map:
        if not kw or len(kw) < 2:
            continue
        idx = text.find(kw)
        if idx < 0:
            # 英文小写别名兼容
            idx = text.lower().find(kw.lower())
        if idx < 0:
            continue
        ctx_start = max(0, idx - 8)
        ctx_end = min(len(text), idx + len(kw) + 8)
        ctx = text[ctx_start:ctx_end]
        if any(w in ctx for w in INDUSTRY_INTENT_WORDS):
            quote = ctx.strip()
            best = (cid, quote)
            break  # 取首个可靠匹配（确定性）
    if best:
        cid, quote = best
        return FieldEvidence(field_name="industry", value=cid, quote=quote,
                             snapshot_ref=snapshot_ref,
                             char_span=_span_of(text, quote),
                             extracted_at=_utcnow(), method="canonical_taxonomy.resolve")
    return FieldEvidence(field_name="industry", value="unknown",
                         null_reason="no_reliable_industry_mapping", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_amount(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    num_unit = re.compile(r"(\d+(?:\.\d+)?)\s*(万元|亿元|元|万|亿)")
    m = num_unit.search(text)
    if not m:
        return FieldEvidence(field_name="amount", value=None,
                             null_reason="no_explicit_amount", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    quote = _window(text, m.start(), m.end(), 40)
    # 禁止由模糊语义推算金额
    if any(tok in quote for tok in AMOUNT_FORBIDDEN_TOKENS):
        return FieldEvidence(field_name="amount", value=None,
                             null_reason="amount_not_explicit_semantics", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    number = float(m.group(1))
    unit = m.group(2)
    mult = UNIT_MULTIPLIER.get(unit, 1)
    normalized = number * mult
    normalized = int(normalized) if normalized == int(normalized) else normalized
    return FieldEvidence(
        field_name="amount",
        value={"raw_text": quote, "normalized_number": normalized, "currency": "CNY"},
        quote=quote, snapshot_ref=snapshot_ref,
        char_span=_span_of(text, quote),
        extracted_at=_utcnow(), method="regex_amount",
    )


def extract_requirements(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    m = re.search(
        r"(申报条件|申请条件|申报要求|申请要求)[:：]?\s*([\s\S]{0,400}?)"
        r"(?=\n{2,}|申报对象|适用企业|申请主体|适用范围|联系电话|$)", text)
    if m:
        req = m.group(0).strip()
        if req:
            return FieldEvidence(field_name="requirements", value=req, quote=req,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, req),
                                 extracted_at=_utcnow(), method="regex_requirements_label")
    return FieldEvidence(field_name="requirements", value=None,
                         null_reason="no_explicit_requirements_section", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_eligibility(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    text = parsed.clean_text
    m = re.search(
        r"(申报对象|适用企业|申请主体|适用范围|申报主体)[:：]?\s*([\s\S]{0,400}?)"
        r"(?=\n{2,}|申报条件|联系电话|$)", text)
    if m:
        elig = m.group(0).strip()
        if elig:
            return FieldEvidence(field_name="eligibility", value=elig, quote=elig,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, elig),
                                 extracted_at=_utcnow(), method="regex_eligibility_label")
    return FieldEvidence(field_name="eligibility", value=None,
                         null_reason="no_explicit_eligibility_section", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_contact(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    # P3-2 第一版暂不自动抽取 contact，即使页面存在也保持 null
    return FieldEvidence(field_name="contact", value=None,
                         null_reason="contact_extraction_deferred_to_P3_3",
                         snapshot_ref=snapshot_ref, extracted_at=_utcnow())


# ── 归一化主入口 ────────────────────────────────────────────────────────
def normalize(parsed: ParsedContent, source_url: str, snapshot_ref: Optional[str] = None,
              fetched_at: Optional[str] = None) -> Candidate:
    sr = snapshot_ref
    ev: dict = {}
    ev["title"] = extract_title(parsed, sr)
    ev["source_url"] = extract_source_url(source_url, sr)
    ev["description"] = extract_description(parsed, sr)
    ev["source_organization"] = extract_source_organization(parsed, sr)
    ev["region"] = extract_region(parsed, sr)
    ev["type"] = extract_type(parsed, sr)
    ev["issue_date"] = extract_issue_date(parsed, sr)
    ev["valid_period"] = extract_valid_period(parsed, sr)
    ev["industry"] = extract_industry(parsed, sr)
    ev["amount"] = extract_amount(parsed, sr)
    ev["requirements"] = extract_requirements(parsed, sr)
    ev["eligibility"] = extract_eligibility(parsed, sr)
    ev["contact"] = extract_contact(parsed, sr)

    candidate = Candidate(
        candidate_id=_candidate_id(source_url, parsed.clean_text),
        pipeline_state="normalized",
        pipeline_history=[
            {"stage": "parse", "at": _utcnow(), "note": f"backend={parsed.parser_backend},"
             f"structure_changed={parsed.structure_changed}"},
            {"stage": "normalize", "at": _utcnow(), "note": "null-safe field extraction"},
        ],
        title=ev["title"].value,
        source_url=ev["source_url"].value or "",
        description=ev["description"].value,
        source_organization=ev["source_organization"].value,
        region=ev["region"].value,
        type=ev["type"].value,
        issue_date=ev["issue_date"].value,
        valid_period=ev["valid_period"].value,
        industry=ev["industry"].value,
        amount=ev["amount"].value,
        requirements=ev["requirements"].value,
        eligibility=ev["eligibility"].value,
        contact=ev["contact"].value,
        provenance=Provenance(source_url=source_url, snapshot_ref=snapshot_ref,
                              fetched_at=fetched_at),
        extracted_fields_evidence=ev,
    )
    return candidate


def run_pipeline(html: str, source_url: str, snapshot_ref: Optional[str] = None,
                 fetched_at: Optional[str] = None,
                 failures_dir: Optional[str] = None) -> "Candidate | ParseFailure":
    """Snapshot → parse → normalize；解析失败时返回（并可选记录）ParseFailure。"""
    try:
        parsed = parse_html(html, source_url, snapshot_ref)
    except ParseError as exc:
        pf = ParseFailure(exc.failure_type, exc.detail, source_url, snapshot_ref, _utcnow())
        if failures_dir is not None:
            record_parse_failure(pf, failures_dir)
        return pf
    return normalize(parsed, source_url, snapshot_ref, fetched_at)
