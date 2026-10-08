"""P6-4 A1 ROUND 1 — fetcher negative / failure-classification coverage (COMMITTED).

Scope: P3-1 Fetcher failure handling. NO modification to fetcher.py.
Named ``tests/test_p4_*`` to escape the global ``.gitignore`` ``test_*.py`` trap.

Redirect handling: ROUND 2 implements redirect-boundary hardening in fetcher.py
(re-validate final response.url against the source registry allowlist, fail-closed
otherwise). The regression tests below pin that behaviour. The Fetcher never
generates a PolicyRule.
"""

import requests
from pathlib import Path
from urllib.parse import urlparse

import pytest

import global_policy_aggregator.pipeline.fetcher as fetcher
from global_policy_aggregator.pipeline.fetcher import (
    Fetcher,
    FAILURE_NOT_ALLOWED,
    FAILURE_TIMEOUT,
    FAILURE_HTTP_4XX,
    FAILURE_HTTP_5XX,
    FAILURE_UNEXPECTED_CONTENT,
)
from global_policy_aggregator.pipeline.source_registry import (
    SourceRegistry,
    SourceEntry,
)

VALID_URL = "https://www.gov.cn/zhengce/2026-03/01/p.html"


def _registry():
    entry = SourceEntry(
        source_id="gov_cn", organization="gov",
        list_url="https://www.gov.cn/list", allowed_domains=("www.gov.cn",),
        enabled=True, fetch_policy={"timeout_seconds": 20},
    )
    return SourceRegistry([entry])


def test_not_caught_by_gitignore_trap():
    import subprocess

    here = Path(__file__).resolve()
    r = subprocess.run(
        ["git", "check-ignore", str(here)],
        cwd=str(here.parents[1]), capture_output=True, text=True,
    )
    assert r.returncode == 1


# disallowed URL (registry-out domain) → FAILURE_NOT_ALLOWED, no success
def test_disallowed_url_rejected(tmp_path):
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch("https://example.com/some/policy")
    assert res.status == "failure"
    assert res.failure_type == FAILURE_NOT_ALLOWED
    assert res.content_hash is None
    assert res.snapshot_ref is None


# unsupported scheme (ftp) → FAILURE_NOT_ALLOWED
def test_unsupported_scheme_rejected(tmp_path):
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch("ftp://www.gov.cn/p")
    assert res.status == "failure"
    assert res.failure_type == FAILURE_NOT_ALLOWED


# timeout → FAILURE_TIMEOUT
def test_timeout_classified(tmp_path, monkeypatch):
    def boom(url, timeout_seconds):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(fetcher, "http_get", boom)
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    assert res.status == "failure"
    assert res.failure_type == FAILURE_TIMEOUT


# HTTP 4xx → FAILURE_HTTP_4XX
def test_http_4xx_classified(tmp_path, monkeypatch):
    class R:
        status_code = 404
        content = b"<html>not found</html>"
        headers = {"Content-Type": "text/html"}

    monkeypatch.setattr(fetcher, "http_get", lambda url, timeout_seconds: R())
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    assert res.status == "failure"
    assert res.failure_type == FAILURE_HTTP_4XX
    assert res.http_status == 404


# HTTP 5xx → FAILURE_HTTP_5XX
def test_http_5xx_classified(tmp_path, monkeypatch):
    class R:
        status_code = 503
        content = b"<html>err</html>"
        headers = {"Content-Type": "text/html"}

    monkeypatch.setattr(fetcher, "http_get", lambda url, timeout_seconds: R())
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    assert res.status == "failure"
    assert res.failure_type == FAILURE_HTTP_5XX
    assert res.http_status == 503


# empty response → FAILURE_UNEXPECTED_CONTENT
def test_empty_response_classified(tmp_path, monkeypatch):
    class R:
        status_code = 200
        content = b""
        headers = {"Content-Type": "text/html"}

    monkeypatch.setattr(fetcher, "http_get", lambda url, timeout_seconds: R())
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    assert res.status == "failure"
    assert res.failure_type == FAILURE_UNEXPECTED_CONTENT


# failure classification: no policy / rule is generated on failure
def test_failure_generates_no_policy(tmp_path, monkeypatch):
    class R:
        status_code = 500
        content = b"x"
        headers = {"Content-Type": "text/html"}

    monkeypatch.setattr(fetcher, "http_get", lambda url, timeout_seconds: R())
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    assert res.status == "failure"
    # 失败绝不产生 content_hash / snapshot_ref（不伪装成功 / 不生成政策）
    assert res.content_hash is None
    assert res.snapshot_ref is None


# success path produces ok + content_hash + snapshot_ref (sanity anchor)
def test_success_path_ok(tmp_path, monkeypatch):
    class R:
        status_code = 200
        content = b"<html>policy text</html>"
        headers = {"Content-Type": "text/html"}

    monkeypatch.setattr(fetcher, "http_get", lambda url, timeout_seconds: R())
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    assert res.status == "ok"
    assert res.content_hash
    assert res.snapshot_ref.startswith("snapshots/")


# redirect bypass ROUND-2 regression anchor: record CURRENT behaviour only
def test_redirect_follows_current_behavior(tmp_path, monkeypatch):
    captured = {}

    def fake_get(url, timeout=None, headers=None, allow_redirects=None):
        captured["allow_redirects"] = allow_redirects

        class R:
            status_code = 200
            content = b"<html>policy</html>"
            headers = {"Content-Type": "text/html"}

        return R()

    # 替换 requests.get 以捕获 http_get 传入的 allow_redirects；
    # 保留真实 requests 模块（Timeout / RequestException 仍需可用）。不修改 fetcher.py。
    monkeypatch.setattr(requests, "get", fake_get)
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_URL)
    # ROUND-2 待办：当前 http_get 使用 allow_redirects=True（重定向被跟随）。
    # 此断言锁定当前行为；ROUND-2 二次校验若改为禁止/显式处理需同步更新本测试。
    assert captured.get("allow_redirects") is True
    assert res.status == "ok"


# ── ROUND 2 redirect boundary hardening regression ─────────────────────
# 所有用例均以 www.gov.cn（registry 白名单内）为起点；通过 monkeypatch
# http_get 让返回的 response.url 反映最终跳转目标，不触发真实网络请求。

VALID_START = "https://www.gov.cn/source"


def _mock_response(url, status_code=200, content=b"<html>policy text</html>"):
    """构造带最终 URL 的假 response（response.url = 重定向终点）。"""
    class R:
        pass
    R.url = url
    R.status_code = status_code
    R.content = content
    R.headers = {"Content-Type": "text/html"}
    return R()


# A. allowed → allowed redirect（同域）：SUCCESS，snapshot/哈希正常
def test_redirect_allowed_to_allowed_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(
        fetcher, "http_get",
        lambda url, timeout_seconds: _mock_response("https://www.gov.cn/final"),
    )
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_START)
    assert res.status == "ok"
    assert res.content_hash
    assert res.snapshot_ref.startswith("snapshots/")
    # 成功路径 provenance 沿用请求 URL（重定向终点已在白名单内，正常放行）
    assert res.url == VALID_START


# B. allowed → disallowed domain redirect：FAIL-closed，无 snapshot/哈希
def test_redirect_allowed_to_disallowed_domain_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(
        fetcher, "http_get",
        lambda url, timeout_seconds: _mock_response("https://external.example/final"),
    )
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_START)
    assert res.status == "failure"
    assert res.failure_type == FAILURE_NOT_ALLOWED
    assert res.content_hash is None
    assert res.snapshot_ref is None


# C. allowed → disallowed scheme (ftp) redirect：FAIL-closed，无成功 snapshot
def test_redirect_allowed_to_disallowed_scheme_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(
        fetcher, "http_get",
        lambda url, timeout_seconds: _mock_response("ftp://external.example/file"),
    )
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_START)
    assert res.status == "failure"
    assert res.failure_type == FAILURE_NOT_ALLOWED
    assert res.content_hash is None
    assert res.snapshot_ref is None


# D. no redirect：普通 allowed URL 正常成功（response.url == 原始 URL）
def test_no_redirect_allowed_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(
        fetcher, "http_get",
        lambda url, timeout_seconds: _mock_response(VALID_START),
    )
    f = Fetcher(_registry(), snapshots_dir=tmp_path / "snap")
    res = f.fetch(VALID_START)
    assert res.status == "ok"
    assert res.content_hash
    assert res.snapshot_ref.startswith("snapshots/")
