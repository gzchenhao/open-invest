"""P4-21 — 最小 LLM Provider 抽象（可替换，不写死 OpenAI）。

- ``LLMProvider``（Protocol）：唯一方法 ``complete(system=, user=) -> str``（LLM 原始文本）。
- ``OpenAICompatibleProvider``：OpenAI-compatible REST（用 requests，无需 openai SDK）。
  API key 仅来自环境变量 ``OPENINVEST_LLM_API_KEY``；绝不写死进仓库 / REAL / Trust /
  fixtures / logs。
- ``FakeProvider``：确定性离线 test double；仅把显式用户文本映射为合法 user-facts JSON，
  **绝不模拟** Eligibility / Benefit / eligible_hired_persons。仅用于测试抽取 adapter
  + 现有确定性执行链。

任何 provider 失败（缺 key / 网络 / 超时 / API error）抛 ``ProviderUnavailable``，
由抽取层 fail-closed（绝不 fallback 到 legacy heuristic，如 investment_capacity_usd*0.15）。
"""
from typing import List, Optional, Protocol, runtime_checkable
import json
import os
import re

try:
    import requests  # 生产 provider 依赖（已在 requirements.txt）
except Exception:  # pragma: no cover
    requests = None


class ProviderUnavailable(Exception):
    """Provider 不可用；抽取层必须 fail-closed，绝不 fallback。"""


@runtime_checkable
class LLMProvider(Protocol):
    def complete(self, *, system: str, user: str) -> str:
        """调用 LLM，返回原始文本（期望 JSON）。失败时抛 ProviderUnavailable。"""
        ...


class OpenAICompatibleProvider:
    """OpenAI-compatible REST provider（API key 仅来自环境变量）。"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini",
                 base_url: Optional[str] = None, timeout: float = 30.0):
        key = api_key or os.environ.get("OPENINVEST_LLM_API_KEY")
        if not key:
            raise ProviderUnavailable(
                "LLM API key 缺失（需设置环境变量 OPENINVEST_LLM_API_KEY）")
        if requests is None:
            raise ProviderUnavailable("requests 不可用（provider 依赖缺失）")
        self._key = key
        self._model = model
        self._base = (base_url or os.environ.get("OPENINVEST_LLM_BASE_URL")
                      or "https://api.openai.com/v1").rstrip("/")
        self._timeout = timeout

    def complete(self, *, system: str, user: str) -> str:
        try:
            resp = requests.post(
                f"{self._base}/chat/completions",
                headers={"Authorization": f"Bearer {self._key}",
                         "Content-Type": "application/json"},
                json={"model": self._model,
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": user}],
                      "response_format": {"type": "json_object"}},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except ProviderUnavailable:
            raise
        except Exception as e:  # 网络 / 超时 / HTTP / 解析错误全部 fail-closed
            raise ProviderUnavailable(f"LLM provider 调用失败：{e}") from e


class FakeProvider:
    """确定性离线 test double（仅测试）。

    只输出用户文本中**显式**出现的 user facts（REAL 122 契约内），绝不模拟
    Eligibility / Benefit / eligible_hired_persons。用于驱动 extractor + adapter +
    现有确定性执行链。不调用任何外部网络。
    """

    def complete(self, *, system: str, user: str) -> str:
        return json.dumps(self._extract(user), ensure_ascii=False)

    def _extract(self, text: str) -> dict:
        facts: List[dict] = []
        unresolved: List[str] = []

        # 主体类型（显式）
        if "个体工商户" in text:
            facts.append({"field": "applicant_entity_type", "value": "个体工商户",
                          "source": "user", "source_text": "个体工商户"})
        elif "企业" in text:
            facts.append({"field": "applicant_entity_type", "value": "企业",
                          "source": "user", "source_text": "企业"})

        # 招用总人数（显式整数）
        m = re.search(r"(\d+)\s*个人", text)
        if m:
            n = int(m.group(1))
            facts.append({"field": "hired_persons", "value": n,
                          "source": "user", "source_text": m.group(0)})
            # 用户声称已符合的人数（非最终合格人数）
            m2 = re.search(r"(\d+)\s*个人(?:已经)?符合", text)
            if m2:
                facts.append({"field": "user_stated_eligible_count",
                              "value": int(m2.group(1)),
                              "source": "user", "source_text": m2.group(0)})

        if "你自己判断" in text or "其他情况" in text:
            unresolved.append("其余资格事实未提供，交由系统判定（不补全）")

        return {"facts": facts, "unresolved": unresolved}
