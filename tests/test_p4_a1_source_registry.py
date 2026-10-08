"""P6-4 A1 ROUND 1 — source_registry fail-closed coverage (COMMITTED).

Scope: P3-0 Source Registry whitelist enforcement. No production code modified.
Named ``tests/test_p4_*`` to escape the global ``.gitignore`` ``test_*.py`` trap.

Verifies: registry 缺失/非法结构 → RegistryError (fail-closed)；非法 scheme；
disallowed domain；allowlist 边界；全新域名不自动放行
（allow_new_domains_automatically=false 的隐含语义）；registry 外 URL 一律拒绝。
"""

import json
from pathlib import Path

import pytest

from global_policy_aggregator.pipeline.source_registry import (
    SourceRegistry,
    SourceEntry,
    RegistryError,
)


def _entry(source_id="gov_cn", organization="gov",
           list_url="https://www.gov.cn/list",
           allowed_domains=("www.gov.cn",), enabled=True, fetch_policy=None):
    return SourceEntry(
        source_id=source_id, organization=organization,
        list_url=list_url, allowed_domains=tuple(allowed_domains),
        enabled=enabled, fetch_policy=dict(fetch_policy or {"timeout_seconds": 20}),
    )


def test_not_caught_by_gitignore_trap():
    import subprocess

    here = Path(__file__).resolve()
    r = subprocess.run(
        ["git", "check-ignore", str(here)],
        cwd=str(here.parents[1]), capture_output=True, text=True,
    )
    assert r.returncode == 1


# ── registry 缺失 / 非法结构 ──────────────────────────────────────────────
def test_registry_missing_raises(tmp_path):
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(tmp_path / "does_not_exist.json")


def test_registry_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


def test_registry_top_not_dict_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


def test_registry_missing_sources_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"foo": "bar"}), encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


def test_registry_source_missing_keys_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"sources": [{"source_id": "x"}]}), encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


def test_registry_empty_allowed_domains_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"sources": [{
        "source_id": "x", "organization": "o", "list_url": "https://a.com/l",
        "allowed_domains": [], "enabled": True, "fetch_policy": {}}]}),
        encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


def test_registry_list_url_bad_scheme_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"sources": [{
        "source_id": "x", "organization": "o", "list_url": "ftp://a.com/l",
        "allowed_domains": ["a.com"], "enabled": True, "fetch_policy": {}}]}),
        encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


def test_registry_duplicate_source_id_raises(tmp_path):
    src = {"source_id": "x", "organization": "o", "list_url": "https://a.com/l",
           "allowed_domains": ["a.com"], "enabled": True, "fetch_policy": {}}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"sources": [src, dict(src)]}), encoding="utf-8")
    with pytest.raises(RegistryError):
        SourceRegistry.from_file(p)


# ── is_url_allowed 行为 ───────────────────────────────────────────────────
def test_is_url_allowed_bad_scheme():
    reg = SourceRegistry([_entry()])
    allowed, reason = reg.is_url_allowed("ftp://www.gov.cn/p")
    assert allowed is False
    assert "HTTP" in reason or "scheme" in reason.lower()


def test_is_url_allowed_disallowed_domain():
    reg = SourceRegistry([_entry()])
    allowed, reason = reg.is_url_allowed("https://example.com/p")
    assert allowed is False
    assert "白名单" in reason or "registry" in reason.lower()


def test_is_url_allowed_exact_match():
    reg = SourceRegistry([_entry(allowed_domains=("www.gov.cn",))])
    allowed, _ = reg.is_url_allowed("https://www.gov.cn/zhengce/p")
    assert allowed is True


def test_is_url_allowed_subdomain_boundary():
    # allowlist 含 www.gov.cn，但裸 gov.cn 不算匹配（子域边界）
    reg = SourceRegistry([_entry(allowed_domains=("www.gov.cn",))])
    allowed, _ = reg.is_url_allowed("https://gov.cn/p")
    assert allowed is False


def test_new_domain_not_auto_allowed():
    # allow_new_domains_automatically=false 的隐含语义：全新域名一律拒绝
    reg = SourceRegistry([_entry(allowed_domains=("www.gov.cn",))])
    allowed, reason = reg.is_url_allowed("https://brandnew.example.org/p")
    assert allowed is False


def test_is_url_allowed_empty():
    reg = SourceRegistry([_entry()])
    allowed, reason = reg.is_url_allowed("")
    assert allowed is False
    assert "URL 为空" in reason


def test_find_source_for_url_returns_none_outside():
    reg = SourceRegistry([_entry(allowed_domains=("www.gov.cn",))])
    assert reg.find_source_for_url("https://example.com/x") is None
    assert reg.find_source_for_url("https://www.gov.cn/y") is not None


# ── 真实生产 registry 可加载（只读，不修改） ──────────────────────────────
def test_production_registry_loads_readonly():
    prod = (Path(__file__).resolve().parents[1]
            / "global_policy_aggregator" / "data" / "real_policies"
            / "source_registry.json")
    if prod.exists():
        reg = SourceRegistry.from_file(prod)  # 必须成功（fail-closed 合法性）
        assert reg.allowed_domains
        # 真实 registry 不应允许 registry 外域名
        allowed, _ = reg.is_url_allowed("https://example.com/x")
        assert allowed is False
