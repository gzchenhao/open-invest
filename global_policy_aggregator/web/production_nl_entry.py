"""P4-23 — Production NL Entry (minimal adapter).

把自然语言项目描述接入**已经过 P4-21 / P4-22 验证**的确定性执行链：

    POST /api/nl/assess  {"nl_text": "..."}
      → extract_and_evaluate(nl_text, policies, trust_service=...)
      → {extracted user facts, unresolved, provenance,
         deterministic eligibility, eligible_hired_persons, benefit, evidence trace}

本模块**仅做入口接线**，绝不重新实现 Eligibility / Benefit / Match / Trust。
真实 LLM Provider 仅从环境变量 ``OPENINVEST_LLM_API_KEY`` 读取；测试通过
``assess()`` 函数注入 ``FakeProvider``，不调用任何真实 LLM。

选择依据：现有入口均为 legacy / demo —— ``server/main.py`` 与 ``client/main.py``
是 JSON-RPC 技术就绪 / 招商服务，与政策 NL 无关；``web/ai_agent_interface.py``
走 legacy ``agents.policy_ai_agent``（含启发式补贴估算），
``web/interactive_ai_server.py`` 是 MOCK 演示门户。因此最小可审计接线是**新建独立
production entry**，直接调用 ``extract_and_evaluate``，不触碰任何 legacy 代码。
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ── repo root 加入 sys.path（使 global_policy_aggregator 与 src 可导入）──
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from global_policy_aggregator.nl_extraction import (  # noqa: E402
    extract_and_evaluate,
    FakeProvider,
    LLMProvider,
    ProviderUnavailable,
)

_REAL_POLICIES_FILE = os.path.join(
    REPO_ROOT, "global_policy_aggregator", "data", "real_policies", "real_policies.json"
)
_PRODUCTION_EVENT_LOG = os.path.join(
    REPO_ROOT, "trust_config", "production_trust_events.jsonl"
)
_PRODUCTION_AUTHORITY_REGISTRY = os.path.join(
    REPO_ROOT, "trust_config", "production_authority_registry.json"
)


def load_real_policies() -> List[Dict[str, Any]]:
    """仅加载 REAL（is_mock is False）政策。任意失败 → []（绝不 crash）。"""
    try:
        with open(_REAL_POLICIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [p for p in data if p.get("is_mock") is False]


def _build_trust_service():
    """生产 Trust 门禁：绑定 Production Event Log + Production Authority Registry，
    并在启动时从 durable REAL 122 Policy Evidence 重建 Context A 的 EvidenceObject
    （P4-25 bootstrap）。只读 VerificationEventLog，**不创建任何新事件**。

    三者（event log / authority registry / Context A evidence source）缺一 → 返回 None
    （orchestrator 把 trust 视为未核验 → 执行阻断，绝不伪造 VERIFIED）。
    不修改 src/trust 或 event log；加载失败也绝不自动 VERIFIED。
    """
    if not os.path.exists(_PRODUCTION_EVENT_LOG):
        return None
    if not os.path.exists(_PRODUCTION_AUTHORITY_REGISTRY):
        return None
    try:
        from src.trust.trust_service import TrustEvidenceService
        from global_policy_aggregator.pipeline.trust_evidence_bootstrap import (
            load_context_a_evidence,
        )
        svc = TrustEvidenceService(
            event_log_path=_PRODUCTION_EVENT_LOG,
            authority_registry_config_path=_PRODUCTION_AUTHORITY_REGISTRY,
        )
        load_context_a_evidence(svc)
        return svc
    except Exception:
        return None


def assess(nl_text: str, *,
           provider: Optional[LLMProvider] = None,
           trust_service: Any = None,
           policies: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """入口可调用的评估函数。**纯接线**：仅转发给 ``extract_and_evaluate``。

    入口**不计算** eligibility / benefit / eligible_hired_persons；
    这些全部由确定性执行链产出。
    """
    pols = policies if policies is not None else load_real_policies()
    return extract_and_evaluate(
        nl_text, pols, trust_service=trust_service, provider=provider
    )


# ── 序列化（保留 provenance；入口绝不重算）──
def _to_jsonable(o: Any) -> Any:
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        return dataclasses.asdict(o)
    if isinstance(o, dict):
        return {k: _to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_to_jsonable(v) for v in o]
    return o


def _serialize(out: Dict[str, Any]) -> Dict[str, Any]:
    """把 extract_and_evaluate 输出转为可 JSON 化的 dict，保留抽取事实来源与证据。"""
    return {
        "extraction": _to_jsonable(out["extraction"]),
        "execution": _to_jsonable(out["execution"]),
        "project_profile": _to_jsonable(out["project_profile"]),
        "project_inputs": _to_jsonable(out["project_inputs"]),
    }


class NLAssessRequest(BaseModel):
    nl_text: str


app = FastAPI(
    title="OpenInvest Production NL Policy Assessor (P4-23)",
    description="Minimal entry wiring NL -> deterministic execution chain. "
                "No legacy agent, no self-computed eligibility/benefit.",
    version="P4-23",
)


@app.post("/api/nl/assess")
async def nl_assess(req: NLAssessRequest):
    if not req.nl_text or not str(req.nl_text).strip():
        raise HTTPException(status_code=400, detail="nl_text required")
    # 生产默认 provider：extract_and_evaluate 内部 OpenAICompatibleProvider（读
    # OPENINVEST_LLM_API_KEY）；缺 key / 网络不可用 → ProviderUnavailable。
    try:
        out = assess(req.nl_text, trust_service=_build_trust_service())
    except ProviderUnavailable as e:
        # 真实 LLM 不可用 → fail-closed：返回结构化失败结果，不 fallback legacy、不自行计算。
        return {
            "extraction": {
                "status": "EXTRACTION_FAILED",
                "facts": [],
                "unresolved": [],
                "error": f"llm provider unavailable: {e}",
            },
            "execution": None,
            "project_profile": None,
            "project_inputs": None,
        }
    except Exception as e:  # 入口不隐藏确定性失败，但也绝不自行计算
        raise HTTPException(status_code=500, detail=f"assessment failed: {e}")
    return _serialize(out)


@app.get("/health")
async def health():
    return {"status": "healthy", "entry": "production_nl_entry", "version": "P4-23"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8018)
