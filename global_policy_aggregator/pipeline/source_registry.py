"""P3-1 Source Registry — 官方来源白名单（P3-0 契约，JUDGE 批准）。

- 只允许官方来源；任何 registry 之外的 URL 必须被 fetcher 拒绝。
- 不自动发现新的外部域名：新源只能人工写入 registry 文件（tracked in Git）。
- fail-closed：registry 文件缺失 / 非法 JSON / 结构不符 → raise，绝不静默放行。
- 本模块与 src/trust/** 零关系；不产生 verification 语义（候选恒 unverified）。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "real_policies" / "source_registry.json"
)

ALLOWED_SCHEMES = ("http", "https")

_REQUIRED_SOURCE_KEYS = (
    "source_id",
    "organization",
    "list_url",
    "allowed_domains",
    "enabled",
    "fetch_policy",
)


class RegistryError(ValueError):
    """registry 文件缺失 / 非法 / 结构不符（fail-closed）。"""


@dataclass(frozen=True)
class SourceEntry:
    source_id: str
    organization: str
    list_url: str
    allowed_domains: tuple
    enabled: bool
    fetch_policy: dict
    last_fetched_at: str | None = None
    notes: str | None = None


def _parse_source(raw: dict) -> SourceEntry:
    missing = [k for k in _REQUIRED_SOURCE_KEYS if k not in raw]
    if missing:
        raise RegistryError(f"source 缺少必需字段 {missing}: {raw.get('source_id', '?')}")
    if not isinstance(raw["allowed_domains"], list) or not raw["allowed_domains"]:
        raise RegistryError(f"allowed_domains 必须是非空 list: {raw['source_id']}")
    scheme = urlparse(raw["list_url"]).scheme
    if scheme not in ALLOWED_SCHEMES:
        raise RegistryError(f"list_url 必须 HTTP/HTTPS: {raw['source_id']}")
    list_host = urlparse(raw["list_url"]).netloc.lower()
    domains = {d.lower() for d in raw["allowed_domains"]}
    if list_host not in domains:
        raise RegistryError(
            f"list_url 域名 {list_host} 不在自己的 allowed_domains 内: {raw['source_id']}"
        )
    policy = raw["fetch_policy"]
    if not isinstance(policy, dict):
        raise RegistryError(f"fetch_policy 必须是 dict: {raw['source_id']}")
    return SourceEntry(
        source_id=raw["source_id"],
        organization=raw["organization"],
        list_url=raw["list_url"],
        allowed_domains=tuple(sorted(domains)),
        enabled=bool(raw["enabled"]),
        fetch_policy=dict(policy),
        last_fetched_at=raw.get("last_fetched_at"),
        notes=raw.get("notes"),
    )


class SourceRegistry:
    """已加载并校验的官方源白名单。"""

    def __init__(self, sources, registry_path=None):
        self.sources = tuple(sources)
        self.registry_path = Path(registry_path) if registry_path else None

    @classmethod
    def from_file(cls, path=None) -> "SourceRegistry":
        registry_path = Path(path) if path else DEFAULT_REGISTRY_PATH
        if not registry_path.exists():
            raise RegistryError(f"registry 文件不存在（fail-closed）: {registry_path}")
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise RegistryError(f"registry JSON 非法: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
            raise RegistryError("registry 顶层必须是含 sources list 的 object")
        sources = [_parse_source(s) for s in data["sources"]]
        ids = [s.source_id for s in sources]
        if len(ids) != len(set(ids)):
            raise RegistryError(f"source_id 重复: {ids}")
        if not sources:
            raise RegistryError("registry 至少需要一个 source")
        return cls(sources, registry_path)

    @property
    def enabled_sources(self) -> tuple:
        return tuple(s for s in self.sources if s.enabled)

    @property
    def allowed_domains(self) -> frozenset:
        """所有 enabled 源的域并集（registry 外域名一律拒绝）。"""
        domains = set()
        for s in self.enabled_sources:
            domains.update(s.allowed_domains)
        return frozenset(domains)

    def is_url_allowed(self, url: str):
        """返回 (allowed: bool, reason: str)。HTTP/HTTPS + enabled 白名单域名。"""
        if not isinstance(url, str) or not url.strip():
            return False, "URL 为空"
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES:
            return False, f"仅允许 HTTP/HTTPS，实际 scheme: {parsed.scheme or '(none)'}"
        host = (parsed.netloc or "").lower()
        if not host:
            return False, "URL 无主机名"
        if host not in self.allowed_domains:
            return False, f"域名 {host} 不在 source registry 白名单（registry 外 URL 必须拒绝）"
        return True, "allowed"

    def find_source_for_url(self, url: str):
        """返回第一个 allowed_domains 覆盖该 URL 域名的 enabled 源；无则 None。"""
        if not isinstance(url, str):
            return None
        host = urlparse(url).netloc.lower()
        for s in self.enabled_sources:
            if host in s.allowed_domains:
                return s
        return None
