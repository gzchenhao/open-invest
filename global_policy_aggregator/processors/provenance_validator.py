#!/usr/bin/env python3
"""
Policy Provenance & Anti-Hallucination Validator（TASK-P0-2）

OpenInvest 数据真实性治理核心模块。最高纪律：
    宁可 null，不要猜。宁可 UNVERIFIED，不要 VERIFIED。
    宁可少一条政策，不要多一条假的政策。

实现规则：
    [DATA-INTEGRITY-001] No Fabricated Government Information
    [DATA-INTEGRITY-002] Every Policy Must Have Provenance
    [DATA-INTEGRITY-003] Every Contact Must Be Verifiable
    [DATA-INTEGRITY-004] Unknown Information Must Remain Unknown
    [DATA-INTEGRITY-005] Mock Data Must Never Resemble Verified Government Data

关键区分（第十五条）：
    url_status（URL 格式/可达性） != source_verification_status（来源真实性）。
    HTTP 200 只能证明 URL 当前可访问，不能证明内容是官方政策。
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """政策核验状态（第七条）"""
    VERIFIED = "verified"                    # 能找到并验证官方来源
    PARTIALLY_VERIFIED = "partially_verified"  # 来源存在，但部分字段无法确认
    UNVERIFIED = "unverified"                # 发现了信息，但没有足够官方证据
    MOCK = "mock"                            # 仅用于 Demo / 开发测试


class UrlStatus(str, Enum):
    """URL 技术性状态 —— 不代表来源真实性"""
    VALID_FORMAT = "valid_format"        # 合法 http/https URL
    INVALID_FORMAT = "invalid_format"    # 非法/格式错误
    PLACEHOLDER = "placeholder"          # 明显占位符（example.com 等）
    MISSING = "missing"                  # 缺失（null/空）


class PolicyContact(BaseModel):
    """政策联系方式 —— 所有字段可选；未知必须为 null，禁止占位猜测（第一条）"""
    name: Optional[str] = Field(default=None, description="联系人姓名；无法确认必须为 null")
    department: Optional[str] = Field(default=None, description="官方部门名称")
    phone: Optional[str] = Field(default=None, description="官方公开电话；AI 推测号码必须为 null")
    email: Optional[str] = Field(default=None, description="官方公开邮箱；AI 猜测邮箱必须为 null")
    address: Optional[str] = Field(default=None, description="官方公开地址")
    contact_source_url: Optional[str] = Field(
        default=None, description="证明以上联系方式的官方页面 URL（第十一条）")
    contact_status: Optional[str] = Field(
        default="unverified",
        description="verified / unverified；无来源证明时必须为 unverified")


class PolicyProvenance(BaseModel):
    """政策溯源模型（第三条）—— 全部字段可选，保证旧数据向后兼容（TEST-PROVENANCE-006）"""
    is_mock: bool = Field(default=False, description="Mock/演示数据必须显式为 true")
    verification_status: Optional[str] = Field(
        default=None, description="verified / partially_verified / unverified / mock")
    source_url: Optional[str] = Field(default=None, description="真实可访问的官方原始来源")
    source_title: Optional[str] = Field(default=None)
    publisher: Optional[str] = Field(default=None, description="发布机构")
    published_date: Optional[str] = Field(default=None, description="无法确认必须为 null，禁止推断")
    effective_date: Optional[str] = Field(default=None, description="无法确认必须为 null，禁止推断")
    retrieved_at: Optional[str] = Field(default=None, description="爬取/录入时间")
    secondary_source_url: Optional[str] = Field(
        default=None, description="第三方辅助发现来源（不得冒充官方来源）")
    url_status: Optional[str] = Field(default=None, description="URL 技术性状态")
    source_verification_status: Optional[str] = Field(
        default=None, description="来源真实性核验状态（与 url_status 严格分开）")
    contact: Optional[PolicyContact] = Field(default=None)


# 明显的占位符 URL 特征（第十四条）
_PLACEHOLDER_URL_PATTERNS = [
    r"example\.(com|org|net|gov\.cn)",
    r"placeholder",
    r"your-?(url|site|domain|link)",
    r"xxx+",
    r"127\.0\.0\.1",
    r"localhost",
    r"\{\{.*\}\}",
    r"<.*>",
]


def validate_source_url(url: Optional[str]) -> Dict[str, Any]:
    """
    URL 技术性校验（第十四条、第十五条）。

    注意：本函数只判断 URL 格式与占位符特征，
    **绝不**因为格式合法就认定来源真实（URL validation != Source verification）。

    返回: {"url_status": UrlStatus, "reason": str}
    """
    if not url or not str(url).strip() or str(url).strip().lower() == "null":
        return {"url_status": UrlStatus.MISSING, "reason": "source_url missing (allowed for mock data)"}

    url_str = str(url).strip()
    if not re.match(r"^https?://", url_str, re.IGNORECASE):
        return {"url_status": UrlStatus.INVALID_FORMAT,
                "reason": f"not an http/https URL: {url_str[:80]}"}

    lowered = url_str.lower()
    for pattern in _PLACEHOLDER_URL_PATTERNS:
        if re.search(pattern, lowered):
            return {"url_status": UrlStatus.PLACEHOLDER,
                    "reason": f"looks like a placeholder URL: {url_str[:80]}"}

    return {"url_status": UrlStatus.VALID_FORMAT,
            "reason": "format valid ONLY — source truthfulness NOT verified"}


def validate_policy_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    对单条政策记录执行数据真实性治理校验。

    规则（对应 TEST-PROVENANCE-001..005）：
    - is_mock=True 的记录，verification_status 不得为 verified / partially_verified
    - verification_status=verified 必须拥有合法且非占位符的 source_url
    - 占位符 / 非法 URL 不得作为 VERIFIED 来源
    - 联系方式若含 phone/email，必须有 contact_source_url，
      或 contact_status 明确为 unverified，或字段本身为 null

    返回: {"valid": bool, "issues": [str, ...], "provenance": PolicyProvenance}
    """
    issues: List[str] = []

    # 兼容性提取：新字段全部可选（旧 payload 无新字段时正常解析，TEST-006）
    is_mock = bool(record.get("is_mock", False))
    verification_status = record.get("verification_status")

    # provenance 可能位于顶层或 metadata 内（两种现有数据形态都支持）
    metadata = record.get("metadata") or {}
    source_url = record.get("source_url", metadata.get("source_url"))

    # ---- 规则 1: Mock 不得被标记为 VERIFIED（TEST-PROVENANCE-001 / DATA-INTEGRITY-005）----
    if is_mock and verification_status in (
            VerificationStatus.VERIFIED.value, VerificationStatus.PARTIALLY_VERIFIED.value):
        issues.append(
            "DATA-INTEGRITY-005 violation: mock policy must not be marked "
            f"'{verification_status}'")

    # ---- 规则 2: VERIFIED 必须拥有合法且非占位符 source_url（TEST-PROVENANCE-003/005）----
    if verification_status == VerificationStatus.VERIFIED.value and not is_mock:
        url_check = validate_source_url(source_url)
        if url_check["url_status"] == UrlStatus.MISSING:
            issues.append("DATA-INTEGRITY-002 violation: VERIFIED policy requires source_url")
        elif url_check["url_status"] == UrlStatus.INVALID_FORMAT:
            issues.append(f"VERIFIED policy has invalid source_url: {url_check['reason']}")
        elif url_check["url_status"] == UrlStatus.PLACEHOLDER:
            issues.append(f"VERIFIED policy has placeholder source_url: {url_check['reason']}")

    # ---- 规则 3: 联系方式必须具备 provenance 或明确 unverified（TEST-PROVENANCE-004）----
    contact = record.get("official_contact") or record.get("contact") \
        or (record.get("application_process") or {}).get("contact_info")
    if isinstance(contact, dict):
        phone = contact.get("phone")
        email = contact.get("email")
        contact_source = contact.get("contact_source_url")
        contact_status = str(contact.get("contact_status") or "unverified").lower()

        has_contact_value = bool((phone and str(phone).strip()) or (email and str(email).strip()))
        if has_contact_value:
            if not contact_source and contact_status != "unverified":
                issues.append(
                    "DATA-INTEGRITY-003 violation: contact has phone/email but no "
                    "contact_source_url and contact_status is not 'unverified'")
            # 电话号码若为典型占位符则直接视为违规（疑似虚构）
            if phone and re.match(r"^\d{3,4}-12345678$|^13800138000$", str(phone).strip()):
                issues.append(
                    f"DATA-INTEGRITY-001 violation: placeholder phone number '{phone}' "
                    "presented as contact")

    # ---- 组装可解析的 provenance 模型（验证旧数据兼容性，TEST-006）----
    provenance = PolicyProvenance(
        is_mock=is_mock,
        verification_status=verification_status,
        source_url=source_url if source_url else None,
        source_title=record.get("source_title") or metadata.get("source_title"),
        publisher=record.get("publisher") or record.get("issuing_authority"),
        published_date=record.get("published_date") or record.get("issue_date"),
        effective_date=record.get("effective_date"),
        retrieved_at=metadata.get("retrieved_at") or metadata.get("crawl_timestamp"),
        contact=PolicyContact(**{k: v for k, v in (contact or {}).items()
                                 if k in PolicyContact.model_fields}) if isinstance(contact, dict) else None,
    )

    return {"valid": len(issues) == 0, "issues": issues, "provenance": provenance}


def audit_policy_dataset(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    对政策数据集执行整体审计（第十六条），只统计不修改：
    TOTAL / MOCK / VERIFIED / UNVERIFIED / MISSING SOURCE URL / MISSING CONTACT PROVENANCE
    """
    stats = {
        "total_records": len(records),
        "mock_records": 0,
        "verified_records": 0,
        "partially_verified_records": 0,
        "unverified_records": 0,
        "unknown_status_records": 0,
        "missing_source_url": 0,
        "missing_contact_provenance": 0,
        "governance_violations": 0,
    }
    for record in records:
        result = validate_policy_record(record)
        if not result["valid"]:
            stats["governance_violations"] += 1
        status = record.get("verification_status")
        if record.get("is_mock"):
            stats["mock_records"] += 1
        elif status == VerificationStatus.VERIFIED.value:
            stats["verified_records"] += 1
        elif status == VerificationStatus.PARTIALLY_VERIFIED.value:
            stats["partially_verified_records"] += 1
        elif status == VerificationStatus.UNVERIFIED.value:
            stats["unverified_records"] += 1
        else:
            stats["unknown_status_records"] += 1

        metadata = record.get("metadata") or {}
        source_url = record.get("source_url", metadata.get("source_url"))
        if not source_url:
            stats["missing_source_url"] += 1

        contact = record.get("official_contact") or record.get("contact") \
            or (record.get("application_process") or {}).get("contact_info")
        if isinstance(contact, dict) and (contact.get("phone") or contact.get("email")) \
                and not contact.get("contact_source_url"):
            stats["missing_contact_provenance"] += 1
    return stats
