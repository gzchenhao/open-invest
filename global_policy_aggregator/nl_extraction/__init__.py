"""P4-21 — Natural Language Fact Extraction 包（最小实现）。

装配链路（LLM 仅做事实抽取，其余交给现有确定性执行链）：
    User NL → NaturalLanguageFactExtractor → LLMProvider
            → 严格 user facts → to_orchestrator_inputs (dict)
            → evaluate_project_against_policies → Match → Eligibility → Benefit

本包不修改 Eligibility / Benefit / Trust / REAL；不调用 legacy agent
（agents.policy_ai_agent / web.ai_agent_interface / client.hooks.ai_agent_direct_apply）。
"""
from typing import Any, Dict, List, Optional

from .contract import (
    ALLOWED_FIELDS, FORBIDDEN_FIELDS, SOURCE_REQUIRED,
)
from .provider import (
    LLMProvider, OpenAICompatibleProvider, FakeProvider, ProviderUnavailable,
)
from .extractor import (
    NaturalLanguageFactExtractor, ExtractedFact, ExtractionResult, ExtractionRejected,
    EXTRACTION_FAILED, NO_FACTS_EXTRACTED, EXTRACTION_OK,
)
from .adapter import to_orchestrator_inputs, ForbiddenFieldError


def extract_and_evaluate(nl_text: str,
                         policies: List[Dict[str, Any]],
                         trust_service: Optional[Any] = None,
                         provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
    """端到端装配：NL → user facts → 现有执行链。

    Returns:
        {"extraction": ExtractionResult, "execution": Optional[list],
         "project_profile": dict, "project_inputs": dict}
        extraction 失败时 execution 为 None。
    """
    prov = provider or OpenAICompatibleProvider()  # 生产默认（env key）；测试注入 FakeProvider
    extr = NaturalLanguageFactExtractor(prov)
    res = extr.extract(nl_text)
    if res.status != EXTRACTION_OK:
        return {"extraction": res, "execution": None,
                "project_profile": None, "project_inputs": None}
    profile, inputs = to_orchestrator_inputs(res)
    # 现有确定性执行链（不重新实现）
    from global_policy_aggregator.pipeline.p4_execution_orchestrator import (
        evaluate_project_against_policies,
    )
    execution = evaluate_project_against_policies(
        profile, policies, project_inputs=inputs, trust_service=trust_service)
    return {"extraction": res, "execution": execution,
            "project_profile": profile, "project_inputs": inputs}


__all__ = [
    "ALLOWED_FIELDS", "FORBIDDEN_FIELDS", "SOURCE_REQUIRED",
    "EXTRACTION_FAILED", "NO_FACTS_EXTRACTED", "EXTRACTION_OK",
    "LLMProvider", "OpenAICompatibleProvider", "FakeProvider", "ProviderUnavailable",
    "NaturalLanguageFactExtractor", "ExtractedFact", "ExtractionResult", "ExtractionRejected",
    "to_orchestrator_inputs", "ForbiddenFieldError", "extract_and_evaluate",
]
