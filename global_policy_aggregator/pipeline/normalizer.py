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

# percentage / cap / floor 语义标记（用于拒绝模糊表述自动生成）
RULE_AMBIGUOUS_TOKENS = ["适当支持", "适当", "原则上", "视情况", "一般不超过", "最高可", "酌情"]

UNIT_MULTIPLIER = {
    "万元": 10_000, "万": 10_000,
    "亿元": 100_000_000, "亿": 100_000_000,
    "元": 1,
}

# ── D3（P4-5.1）：字段级 rule/benefit 上下文约束 ──────────────────────────
# percentage 必须落在「受益/规则」语境中（否则不得作为 benefit percentage），
# 且必须排除资格阈值语境——例如「裁员率不高于…20%」「全国城镇调查失业率
# 控制目标」是 eligibility threshold，绝不是受益比例。
PERCENTAGE_BENEFIT_TOKENS = (
    "返还", "补贴", "补助", "奖励", "资助", "贴息", "减按", "加计扣除",
    "税前扣除", "优惠", "减免", "抵免", "抵减", "退还", "退税", "提取",
    "计提", "费率", "税率",
)
PERCENTAGE_THRESHOLD_TOKENS = (
    "裁员率", "失业率", "调查失业率", "控制目标", "占比", "不低于",
    "不少于", "不高于", "参保职工总数", "收入占", "比例不低于",
)

# amount 必须落在受益语境中（同一 clause 内），否则不得作为受益金额。
AMOUNT_BENEFIT_TOKENS = (
    "补贴", "补助", "返还", "奖励", "资助", "贴息", "发放", "金额",
    "支持", "保费", "补偿",
)

# 金额计量（per-unit）后缀：将「每招用1人…1500元」识别为「元/人」，
# 避免把按人次计的固定金额误当成一次性总额。
PER_UNIT_PATTERNS = (
    ("每招用1人", "元/人"), ("每人", "元/人"), ("每名", "元/人"),
    ("每户", "元/户"), ("每辆", "元/辆"), ("每台", "元/台"),
    ("每头", "元/头"), ("每次", "元/次"), ("每平方米", "元/平方米"),
)

# 国家级适用范围标记（必须有 verbatim Evidence 才可记录 region="全国"）。
# D3 纪律：只接受「明确适用范围」表述（适用范围/适用于全国…），
# **不接受公文主送机关**（如「各省、自治区、直辖市人民政府」）——主送机关是
# 收件方名单，不是适用范围；把主送机关当作 region 证据属 fail-open。
NATIONAL_SCOPE_PATTERNS = (
    r"全国范围内(?:适用|执行|实施)",
    r"(?:适用于|适用|执行|实施)(?:于)?全国(?:范围)?",
    r"(?:在)?全国(?:范围内)?(?:统一)?(?:适用|执行|实施)",
    r"适用(?:范围)?[:：]\s*全国",
)

# 显式计算基数标签（须原文显式书写，不做推断）。
BASE_LABEL_PATTERN = r"(?:计税依据|计税基数|计算基数|计算依据|计费基数)"
BASE_DEFINITION_TOKENS = ("应纳税所得额", "应纳所得税额")
# 基数捕获后的前导修饰词（属上限/口径修饰，不属于基数本身）。
BASE_LEADING_MODIFIERS = ("不超过", "不高于", "不低于", "按照", "按")

# 常见结构化 eligibility 条件模式（确定性正则，evidence-bound）
ELIGIBILITY_CONDITION_PATTERNS = [
    # (id, source_field, operator, threshold, regex, capture_desc)
    ("registered_years_min", "years_registered", ">=", 1.0,
     r"注册(?:成立)?(?:满|一年以上|1年以上|不少于1年)", "成立满一年"),
    ("rd_staff_ratio_min", "rd_staff_ratio", ">=", 0.10,
     r"科技人员占[^。；]*?比例不低于\s*(\d+(?:\.\d+)?)\s*%", "研发人员比例"),
    ("hightech_income_ratio_min", "hightech_income_ratio", ">=", 0.60,
     r"高新技术产品（服务）收入占[^。；]*?比例不低于\s*(\d+(?:\.\d+)?)\s*%", "高新收入比例"),
]

# G2: 引用型（非数值阈值）eligibility 条件模式（确定性正则，evidence-bound）。
# 治理纪律：仅在「政策自身原文」明确表达受益主体类别时抽取。
# 本法律正文未枚举高新技术企业认定条件 → 绝不从此处注入其他法规
# （实施条例 / 认定管理办法）中的条件；若未来需要，必须作为独立官方政策来源处理。
# (id, source_field, operator, expected_value, regex, capture_desc)
ELIGIBILITY_REFERENCE_CONDITION_PATTERNS = [
    ("state_key_supported_high_tech_enterprise", "is_high_tech_enterprise", "equals", True,
     r"国家需要重点扶持的高新技术企业，\s*减按\s*\d+(?:\.\d+)?\s*[％%]\s*的税率征收企业所得税",
     "国家需要重点扶持的高新技术企业"),
]


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


# D3: 同一 rule/条款上下文的边界字符（与既有 clause 语义保持一致）。
_CLAUSE_BOUNDARIES = "。；！？\n"


def _clause_span(text: str, idx: int) -> Tuple[int, int]:
    """返回包含 idx 的 clause 区间 [start, end)（边界：。；！？\\n）。"""
    start = 0
    for i in range(min(idx, len(text))):
        if text[i] in _CLAUSE_BOUNDARIES:
            start = i + 1
    end = len(text)
    for i in range(idx, len(text)):
        if text[i] in _CLAUSE_BOUNDARIES:
            end = i + 1
            break
    return start, end


def _per_unit_suffix(clause: str) -> Optional[str]:
    """从 clause 中识别 per-unit 计量（如「每招用1人」→ 元/人）。"""
    for kw, suffix in PER_UNIT_PATTERNS:
        if kw in clause:
            return suffix
    return None


# ── D3（P4-5.1）：rule-level 字段的「同一 rule/条款上下文」选择 ───────────
_NUM_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(万元|亿元|元|万|亿)")
_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(％|%)")


def _pct_occurrences(text: str) -> list:
    """收集全部百分比出现，并标注其 clause / 语境类型（确定性，无状态）。"""
    occ = []
    for m in _PCT_RE.finditer(text):
        cs, ce = _clause_span(text, m.start())
        clause = text[cs:ce].strip()
        occ.append({
            "value": float(m.group(1)) / 100.0,
            "raw": m.group(1) + m.group(2),
            "clause": clause,
            "clause_span": (cs, ce),
            "span": (m.start(), m.end()),
            "preferential": bool(re.search(r"减按", clause)),
            "standard": bool(re.search(r"税率\s*为", clause)),
            "threshold": any(tok in clause for tok in PERCENTAGE_THRESHOLD_TOKENS),
            "benefit": any(tok in clause for tok in PERCENTAGE_BENEFIT_TOKENS),
        })
    return occ


def _chosen_pct_occurrence(text: str) -> Optional[dict]:
    """确定性选择「受益百分比」出现；无合格候选 → None（fail-closed）。

    1) 仅保留同时满足「受益/规则语境」且「非 eligibility 阈值」的百分比：
       裁员率 / 失业率 / 控制目标 / 参保职工总数 / 不低于 等阈值一律排除；
    2) 优惠税率（减按 X% 的税率）优先，多个 → doc order 最后一个；
    3) 其余 → 首个非基准税率（保留单比例政策 first-match 行为）；
    4) 无候选 → None —— 绝不把资格阈值当成受益比例，绝不猜。
    """
    eligible = [o for o in _pct_occurrences(text) if o["benefit"] and not o["threshold"]]
    if not eligible:
        return None
    pref = [o for o in eligible if o["preferential"]]
    if pref:
        return pref[-1]
    non_std = [o for o in eligible if not o["standard"]]
    return non_std[0] if non_std else eligible[0]


def _amount_occurrences(text: str) -> list:
    """收集全部「数字+货币单位」出现，并标注其 clause / 是否受益语境。"""
    occ = []
    for m in _NUM_UNIT_RE.finditer(text):
        cs, ce = _clause_span(text, m.start())
        clause = text[cs:ce].strip()
        mult = UNIT_MULTIPLIER.get(m.group(2), 1)
        normalized = float(m.group(1)) * mult
        occ.append({
            "value": int(normalized) if normalized == int(normalized) else normalized,
            "unit": m.group(2),
            "clause": clause,
            "clause_span": (cs, ce),
            "span": (m.start(), m.end()),
            "per_unit": _per_unit_suffix(clause),
            "benefit": any(tok in clause for tok in AMOUNT_BENEFIT_TOKENS),
            "forbidden": any(tok in clause for tok in AMOUNT_FORBIDDEN_TOKENS),
        })
    return occ


def _chosen_amount_occurrence(text: str) -> Optional[dict]:
    """确定性选择「受益金额」出现：doc order 首个「受益语境且非禁止语义」金额。

    要求金额与其 quote **同属一个 clause**（不得跨条款借用证据）；
    无合格候选 → None（绝不猜）。
    """
    for o in _amount_occurrences(text):
        if o["benefit"] and not o["forbidden"]:
            return o
    return None


def _rule_context_clause(text: str) -> Optional[str]:
    """当前 Candidate 的 rule-level 字段所处 clause（同一 rule/条款上下文）。

    优先级：受益百分比 clause（乘数型规则）→ 受益金额 clause（定额型规则）→ None。
    """
    pct = _chosen_pct_occurrence(text)
    if pct is not None:
        return pct["clause"]
    amt = _chosen_amount_occurrence(text)
    if amt is not None:
        return amt["clause"]
    return None


def _strip_base_modifiers(base: str) -> str:
    """剥离基数捕获结果的前导口径修饰词（如「不超过」「按」）。"""
    out = base.strip()
    changed = True
    while changed:
        changed = False
        for mod in BASE_LEADING_MODIFIERS:
            if out.startswith(mod) and len(out) > len(mod):
                out = out[len(mod):].strip()
                changed = True
    return out


def _base_in_clause(clause: str) -> Optional[str]:
    """在**同一 clause** 内寻找显式基数表述（如「按 X 的 Y%」「以 X 为计税依据」）。"""
    if not clause:
        return None
    m = re.search(
        r"(?:" + BASE_LABEL_PATTERN + r"|以|按)[:：]?\s*"
        r"([\u4e00-\u9fa5A-Za-z（）()]{2,30}?)"
        r"(?:为\s*(?:基数|" + BASE_LABEL_PATTERN + r")|的\s*\d+(?:\.\d+)?\s*[%％])",
        clause)
    if not m:
        return None
    base = _strip_base_modifiers(m.group(1))
    return base or None


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
    # 优先级：官方 <h1> / <title> 优先于正文《...》交叉引用。
    # 理由：正文里常出现其他法律/文件的《书名号》引用（如《税收征收管理法》），
    # 不得因此误将交叉引用当作本政策标题。仅当候选能在 snapshot clean text 中
    # 定位（char_span 可验证）时才采用，否则回退到下一个候选。
    candidates = []
    if parsed.h1_raw:
        candidates.append(parsed.h1_raw)
    if parsed.title_raw:
        candidates.append(parsed.title_raw)
    m = re.search(r"《([^》]{2,60})》", parsed.clean_text)
    if m:
        candidates.append(m.group(1))
    for cand in candidates:
        cand = cand.strip()
        if not cand:
            continue
        span = _span_of(parsed.clean_text, cand)
        if span is None and len(candidates) > 1:
            # 该候选不在 clean text（例如 <title> 含站点后缀），跳过往后选
            continue
        return FieldEvidence(
            field_name="title", value=cand, quote=cand,
            snapshot_ref=snapshot_ref,
            char_span=span,
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
    # 纪律（Fix 3）：优先使用页面正文、明确发布机关字段或可靠页面 metadata；
    # 不得仅凭 footer / 模板区域（如「主办单位」）推断；无足够 Evidence 时宁可 null。
    patterns = [
        r"(发布机关|发布单位|发文机关|制定机关|发布部门|来源)[:：]\s*([\u4e00-\u9fa5A-Za-z（）()·0-9]+)",
        r"([\u4e00-\u9fa5]{2,20}?(?:部|委员会|局|厅|办公厅|署))\s*(?:关于印发|发布|颁布|公布)",
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
    # 2) D3: 明确的「全国适用」上下文（必须有 verbatim Evidence 才可记录）。
    for pat in NATIONAL_SCOPE_PATTERNS:
        m_nat = re.search(pat, text)
        if m_nat:
            return FieldEvidence(field_name="region", value="全国",
                                 quote=m_nat.group(0).strip(),
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, m_nat.group(0).strip()),
                                 extracted_at=_utcnow(), method="regex_national_scope")
    # 3) 仅以「政策自身标题 / H1」中的明确行政区划为辖区证据（不做层级推断）。
    #    D3 修复：旧实现把正文开头 200 字也纳入扫描，导致公文主送机关
    #    「各省、自治区、直辖市人民政府」被误判为 region="直辖市"——把全国性
    #    政策缩窄为直辖市，属 fail-open 错误。正文中的行政区划词不再作为
    #    region 证据；无标题级证据时宁可 null。
    search_scope = (parsed.title_raw or "") + "\n" + (parsed.h1_raw or "")
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
    # 1) 显式「起-止」区间（两端日期均由原文提供）
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
    # 1b) D3: 区间右端省略年份的官方写法（「2026年1月1日至12月31日」）——
    #     右端年份**继承左端**（这是原文的书写省略，不是推断）；若右端早于左端
    #     则判定为可疑区间，fail-closed：保留 start，end 保持 null。
    m_short = re.search(
        r"((?:19|20)\d{2})年(\d{1,2})月(\d{1,2})日"
        r"\s*(?:至|—|~|到|起至|止)\s*"
        r"(\d{1,2})月(\d{1,2})日", text)
    if m_short:
        year = int(m_short.group(1))
        start = _norm_date(m_short.group(0))
        end = f"{year:04d}-{int(m_short.group(4)):02d}-{int(m_short.group(5)):02d}"
        quote = m_short.group(0).strip()
        if start and end >= start:
            return FieldEvidence(
                field_name="valid_period", value={"start": start, "end": end},
                quote=quote, snapshot_ref=snapshot_ref,
                char_span=_span_of(text, quote),
                extracted_at=_utcnow(), method="regex_valid_period_shared_year",
            )
        return FieldEvidence(
            field_name="valid_period", value={"start": start, "end": None},
            quote=quote, snapshot_ref=snapshot_ref, char_span=_span_of(text, quote),
            extracted_at=_utcnow(), method="regex_valid_period_shared_year_suspect",
        )
    # 2) G4: 单端起算（官方原文仅给出生效/施行起始日）→ end 保持 null。
    #    治理纪律：绝不推断、绝不使用当前日期、绝不宣称「永久有效」。
    m2 = re.search(
        r"(?:自|从)\s*"
        r"((?:19|20)\d{2}年\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})"
        r"\s*起\s*(?:施行|实施|执行|生效)", text)
    if m2:
        start = _norm_date(m2.group(1))
        if start:
            return FieldEvidence(
                field_name="valid_period", value={"start": start, "end": None},
                quote=m2.group(0).strip(), snapshot_ref=snapshot_ref,
                char_span=_span_of(text, m2.group(0).strip()),
                extracted_at=_utcnow(), method="regex_valid_period_start_only",
            )
    # 3) 无任何明确生效日期 → null（禁止默认 end_date）
    return FieldEvidence(field_name="valid_period", value=None,
                         null_reason="no_explicit_valid_period_start", snapshot_ref=snapshot_ref,
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
    """抽取受益金额（D3：clause 内受益语境 + 同条款 evidence，fail-closed）。

    D3 修复：
    - 金额必须与其 **quote 同属一个 clause**（旧实现用 ±40 字窗口，quote 会跨到
      下一条款，导致下游把「技能提升补贴」的语境套在扩岗补助金额上 = 证据污染）；
    - 必须落在受益语境（补贴/补助/返还/发放/支持…）内，否则 null；
    - 命中禁止语义（比例/按投资/原则上/据实…）→ null（不得由模糊表述推算金额）；
    - per-unit 计量（「每招用1人…1500元」）→ 携带 元/人 量纲，避免把按人次计的
      补助误读为一次性总额；
    - 无合格候选 → null（绝不猜）。
    """
    text = parsed.clean_text
    occ = _amount_occurrences(text)
    if not occ:
        return FieldEvidence(field_name="amount", value=None,
                             null_reason="no_explicit_amount", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    chosen = _chosen_amount_occurrence(text)
    if chosen is None:
        # 存在金额数字，但没有任何一个处在受益语境 / 全部命中禁止语义 → fail-closed。
        reason = ("amount_not_explicit_semantics"
                  if any(o["benefit"] for o in occ) else "amount_not_in_benefit_context")
        return FieldEvidence(field_name="amount", value=None,
                             null_reason=reason, snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    quote = chosen["clause"]
    value = {"raw_text": quote, "normalized_number": chosen["value"], "currency": "CNY"}
    if chosen["per_unit"]:
        value["unit"] = chosen["per_unit"]
    return FieldEvidence(
        field_name="amount", value=value, quote=quote, snapshot_ref=snapshot_ref,
        char_span=_span_of(text, quote) or chosen["clause_span"],
        extracted_at=_utcnow(), method="regex_amount_clause_scoped",
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


# ── P3-2.x Rule Evidence 抽取器（evidence-bound；无明确原文 → null）──────
def _clause_of(text: str, idx: int) -> str:
    """返回包含 idx 的句子片段（以 。；！？\\n 为边界），用于把百分比关联到其 clause。"""
    bounds = [i for i, ch in enumerate(text) if ch in "。；！？\n"]
    start = 0
    for b in bounds:
        if b < idx:
            start = b + 1
        else:
            break
    end = len(text)
    for b in bounds:
        if b > idx:
            end = b + 1
            break
    return text[start:end].strip()


def extract_percentage(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """抽取政策百分比（税率/补贴比例），以比例小数存储（15% → 0.15）。

    通用、evidence-bound 逻辑（不 hardcode 任意具体百分比）：
    - 收集网页中所有百分比出现，每个关联其所在 clause 上下文；
    - 排除 eligibility 阈值百分比（「比例不低于/不少于 X%」「占比 X%」等），
      这些不是政策优惠比例；
    - 优先选择「优惠税率」clause（含「减按 X% 的税率」），排除法定基准税率
      （「税率为 X%」），避免把无关基准税率（如企业所得税 25%）误当作政策百分比；
    - 当存在多个优惠税率时，选取 doc order 中最后一个（最具体 / 末位列出的国家级
      优惠条款）；否则回退到首个显著政策比例（保留单比例政策的 first-match 行为）；
      并以 clause 原文作为 quote，建立 percentage↔clause 的证据关联。
    """
    text = parsed.clean_text
    occ = _pct_occurrences(text)
    if not occ:
        return FieldEvidence(field_name="percentage", value=None,
                             null_reason="no_explicit_percentage", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    # D3 fail-closed：只有「受益/规则语境」中的百分比才可作为受益比例；
    # 资格阈值（裁员率/失业率/控制目标/参保职工总数/不低于…）一律不得当作受益比例。
    chosen = _chosen_pct_occurrence(text)
    if chosen is None:
        return FieldEvidence(field_name="percentage", value=None,
                             null_reason="percentage_no_benefit_context",
                             snapshot_ref=snapshot_ref, extracted_at=_utcnow())
    quote = chosen["clause"]
    span = _span_of(text, quote) or chosen["span"]
    if span is None:
        quote = chosen["raw"]
        span = chosen["span"]
    if any(tok in quote for tok in RULE_AMBIGUOUS_TOKENS):
        return FieldEvidence(field_name="percentage", value=None,
                             null_reason="percentage_not_explicit_semantics",
                             snapshot_ref=snapshot_ref, extracted_at=_utcnow())
    return FieldEvidence(field_name="percentage", value=chosen["value"], quote=quote,
                         snapshot_ref=snapshot_ref, char_span=span,
                         extracted_at=_utcnow(), method="regex_percentage")


def extract_base(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """抽取明确计算基数（D3：同一 rule/条款上下文；无显式原文 → null）。

    D3 修复：
    - 基数必须与**受益百分比处于同一 clause**（同一 rule 上下文）——旧实现全库扫描，
      会把其它条款里出现的基数借给本条款，属跨条款证据污染；
    - 定额 / 按人次金额（fixed_amount / per-unit）**绝不强行猜测基数**；
    - 税务类定义式基数（「…，为应纳税所得额。」）仅在原文显式定义时采纳，
      且 quote 为该定义 clause（而非裸词）；
    - 全部不成立 → null（绝不猜）。
    """
    text = parsed.clean_text
    pct = _chosen_pct_occurrence(text)
    if pct is not None:
        same_clause = _base_in_clause(pct["clause"])
        if same_clause:
            return FieldEvidence(
                field_name="base", value=same_clause, quote=pct["clause"],
                snapshot_ref=snapshot_ref,
                char_span=_span_of(text, pct["clause"]) or pct["clause_span"],
                extracted_at=_utcnow(), method="regex_base_same_clause",
            )
    # 显式基数定义（「以 X 为计税依据 / 计税基数：X」）——原文书写，非推断。
    m = re.search(
        r"以\s*([\u4e00-\u9fa5A-Za-z（）()]{2,30}?)\s*为\s*" + BASE_LABEL_PATTERN, text)
    if not m:
        m = re.search(BASE_LABEL_PATTERN + r"[:：]\s*([\u4e00-\u9fa5A-Za-z（）()]{2,30})", text)
    if m:
        base = _strip_base_modifiers(m.group(1))
        if base:
            cs, ce = _clause_span(text, m.start())
            clause = text[cs:ce].strip() or base
            return FieldEvidence(field_name="base", value=base, quote=clause,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, clause),
                                 extracted_at=_utcnow(), method="regex_base_definition")
    # 定义式税务基数（原文显式定义「…，为应纳税所得额。」）。
    for tok in BASE_DEFINITION_TOKENS:
        m2 = re.search(r"为\s*" + re.escape(tok), text)
        if m2:
            cs, ce = _clause_span(text, m2.start())
            clause = text[cs:ce].strip() or tok
            return FieldEvidence(field_name="base", value=tok, quote=clause,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, clause),
                                 extracted_at=_utcnow(),
                                 method="regex_base_definitional")
    return FieldEvidence(field_name="base", value=None,
                         null_reason="no_explicit_base", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_cap(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """抽取明确上限（如『不超过 X%』『费率上限 X%』）。模糊表述 → null。

    D3：上限必须与当前 rule 上下文（受益百分比 / 受益金额所在 clause）一致，
    不得从其它条款借用上限；无 rule 上下文时保持原有全库行为。
    """
    text = parsed.clean_text
    rule_clause = _rule_context_clause(text)
    scope = rule_clause or text
    m = re.search(
        r"(?:不超过|上限|最高|费率上限|补贴上限)\s*(\d+(?:\.\d+)?)\s*(%|％)",
        scope)
    if not m:
        return FieldEvidence(field_name="cap", value=None,
                             null_reason="no_explicit_cap", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    quote = rule_clause or _window(text, m.start(), m.end(), 30)
    if any(tok in quote for tok in RULE_AMBIGUOUS_TOKENS) and "上限" not in quote:
        return FieldEvidence(field_name="cap", value=None,
                             null_reason="cap_not_explicit_semantics",
                             snapshot_ref=snapshot_ref, extracted_at=_utcnow())
    value = float(m.group(1)) / 100.0
    return FieldEvidence(
        field_name="cap", value=value, quote=quote,
        snapshot_ref=snapshot_ref, char_span=_span_of(text, quote),
        extracted_at=_utcnow(), method="regex_cap",
    )


def extract_floor(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """抽取明确下限（如『不低于 X 元』『保底 X』）。

    仅当上下文出现受益类关键词（补贴/补偿/保费/金额/资助/补助/下限/保底）
    才抽取，避免把 eligibility 比例阈值（如『研发人员比例不低于10%』）误当 floor。
    """
    text = parsed.clean_text
    # D3：下限必须与当前 rule 上下文（受益百分比 / 受益金额所在 clause）一致，
    #     不得从资格条款等其它 clause 借用下限证据。
    rule_clause = _rule_context_clause(text)
    scope = rule_clause or text
    m = re.search(
        r"(?:不低于|不少于|最少|至少)\s*(\d+(?:\.\d+)?)\s*(%|％)?", scope)
    if not m:
        return FieldEvidence(field_name="floor", value=None,
                             null_reason="no_explicit_floor", snapshot_ref=snapshot_ref,
                             extracted_at=_utcnow())
    quote = rule_clause or _window(text, m.start(), m.end(), 40)
    if not any(k in quote for k in
               ("补贴", "补偿", "保费", "金额", "资助", "补助", "下限", "保底", "万元", "元")):
        return FieldEvidence(field_name="floor", value=None,
                             null_reason="floor_not_in_benefit_context",
                             snapshot_ref=snapshot_ref, extracted_at=_utcnow())
    value = float(m.group(1)) / 100.0 if m.group(2) else float(m.group(1))
    return FieldEvidence(
        field_name="floor", value=value, quote=quote,
        snapshot_ref=snapshot_ref, char_span=_span_of(text, quote),
        extracted_at=_utcnow(), method="regex_floor",
    )


def extract_unit(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """抽取单位（元/万元/元每计量对象）。无明确单位 → null（不猜测）。

    D3：若受益金额是 per-unit 计量（「每招用1人…1500元」），单位必须携带 /人 量纲，
    否则下游会把按人次计的补助误读为一次性总额。
    D3 字段一致性：**没有受益金额就没有单位**——unit 必须与 amount 同属一个 rule 上下文；
    否则（amount 为 null 而 unit 非 null）下游会由 unit 反推不存在的金额 = fail-open。
    """
    text = parsed.clean_text
    amt = _chosen_amount_occurrence(text)
    if amt is None:
        return FieldEvidence(field_name="unit", value=None,
                             null_reason="no_unit_without_benefit_amount",
                             snapshot_ref=snapshot_ref, extracted_at=_utcnow())
    if amt["per_unit"]:
        return FieldEvidence(
            field_name="unit", value=amt["per_unit"], quote=amt["clause"],
            snapshot_ref=snapshot_ref,
            char_span=_span_of(text, amt["clause"]) or amt["clause_span"],
            extracted_at=_utcnow(), method="regex_unit_per_unit",
        )
    for unit in ("万元", "亿元", "元"):
        if unit in text:
            return FieldEvidence(field_name="unit", value=unit, quote=unit,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, unit),
                                 extracted_at=_utcnow(), method="regex_unit")
    return FieldEvidence(field_name="unit", value=None,
                         null_reason="no_explicit_unit", snapshot_ref=snapshot_ref,
                         extracted_at=_utcnow())


def extract_currency(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """币种：默认 CNY。仅当原文显式出现外币才取，否则 null（沿用 amount 的 CNY）。"""
    text = parsed.clean_text
    for cur, label in (("美元", "USD"), ("港币", "HKD"), ("欧元", "EUR"), ("日元", "JPY")):
        if cur in text:
            return FieldEvidence(field_name="currency", value=label, quote=cur,
                                 snapshot_ref=snapshot_ref,
                                 char_span=_span_of(text, cur),
                                 extracted_at=_utcnow(), method="regex_currency")
    return FieldEvidence(field_name="currency", value=None,
                         null_reason="default_cny_no_explicit_foreign_currency",
                         snapshot_ref=snapshot_ref, extracted_at=_utcnow())


def extract_eligibility_conditions(parsed: ParsedContent, snapshot_ref: Optional[str]) -> FieldEvidence:
    """结构化 eligibility 条件（确定性正则；每条 evidence-bound）。无 → null list。"""
    text = parsed.clean_text
    conds = []
    for cid, src_field, op, thr, pat, desc in ELIGIBILITY_CONDITION_PATTERNS:
        m = re.search(pat, text)
        if not m:
            continue
        quote = m.group(0).strip()
        # 若正则捕获到阈值，则用捕获阈值覆盖默认（仍须与原文一致）
        threshold = thr
        if m.lastindex and m.groups() and m.group(1) is not None and re.search(r"\d", m.group(1)):
            try:
                threshold = float(m.group(1)) / 100.0
            except ValueError:
                threshold = thr
        conds.append({
            "id": cid,
            "label": desc,
            "source_field": src_field,
            "operator": op,
            "threshold": threshold,
            "quote": quote,
            "char_span": list(_span_of(text, quote) or (None, None)),
            "snapshot_ref": snapshot_ref,
        })
    # G2: 引用型条件（boolean / 分类 equals）——仅当政策原文明确表达受益主体类别。
    for cid, src_field, op, expected, pat, desc in ELIGIBILITY_REFERENCE_CONDITION_PATTERNS:
        m = re.search(pat, text)
        if not m:
            continue
        quote = m.group(0).strip()
        conds.append({
            "id": cid,
            "label": desc,
            "source_field": src_field,
            "operator": op,
            "expected_value": expected,
            "quote": quote,
            "char_span": list(_span_of(text, quote) or (None, None)),
            "snapshot_ref": snapshot_ref,
        })
    if not conds:
        return FieldEvidence(field_name="eligibility_conditions", value=None,
                             null_reason="no_structured_eligibility_conditions",
                             snapshot_ref=snapshot_ref, extracted_at=_utcnow())
    # quote 必须能在 snapshot clean text 中找到（取第一条条件的 verbatim quote）。
    first_quote = conds[0]["quote"]
    return FieldEvidence(field_name="eligibility_conditions", value=conds,
                         quote=first_quote,
                         snapshot_ref=snapshot_ref,
                         char_span=conds[0]["char_span"],
                         extracted_at=_utcnow(), method="regex_eligibility_conditions")


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
    # ── P3-2.x Rule Evidence ──
    ev["percentage"] = extract_percentage(parsed, sr)
    ev["base"] = extract_base(parsed, sr)
    ev["cap"] = extract_cap(parsed, sr)
    ev["floor"] = extract_floor(parsed, sr)
    ev["unit"] = extract_unit(parsed, sr)
    ev["currency"] = extract_currency(parsed, sr)
    ev["eligibility_conditions"] = extract_eligibility_conditions(parsed, sr)
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
        percentage=ev["percentage"].value,
        base=ev["base"].value,
        cap=ev["cap"].value,
        floor=ev["floor"].value,
        unit=ev["unit"].value,
        currency=ev["currency"].value,
        eligibility_conditions=ev["eligibility_conditions"].value,
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
