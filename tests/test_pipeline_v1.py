#!/usr/bin/env python3
"""
P3-1 SOURCE REGISTRY + FETCHER + SNAPSHOT 测试（JUDGE 批准范围）。

契约要点：
- registry allowlist：registry 外域名 / 非 HTTP(S) 一律拒绝
- User-Agent 明示 OpenInvest-PolicyResearch/1.0；不伪装浏览器
- 有限重试、失败类型六分类、失败不产生 policy、不伪装成功
- snapshot：content_hash 去重、retrieved_at UTC、runtime artifact 不进 Git
- Trust 隔离：不 import src/trust/**、无 VERIFIED / verification_status
- 现有 20 条 REAL 不变
- 全部使用 mock HTTP（CI 无真实网络依赖）
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from global_policy_aggregator.pipeline import fetcher as fetcher_mod  # noqa: E402
from global_policy_aggregator.pipeline.fetcher import (  # noqa: E402
    Fetcher,
    compute_content_hash,
    normalize_content,
)
from global_policy_aggregator.pipeline.source_registry import (  # noqa: E402
    RegistryError,
    SourceRegistry,
    DEFAULT_REGISTRY_PATH,
)

GOV_URL = "https://www.gov.cn/zhengce/zhengceku/202401/content_6925101.htm"
SAMPLE_HTML = b"<html><body>\xe6\x94\xbf\xe7\xad\x96\xe5\x86\x85\xe5\xae\xb9</body></html>"  # 政策内容


class FakeResponse:
    def __init__(self, status_code=200, content=SAMPLE_HTML, headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}


@pytest.fixture
def registry():
    return SourceRegistry.from_file()  # 真实 tracked registry（gov.cn）


@pytest.fixture
def fetcher(registry, tmp_path, monkeypatch):
    sleeps = []
    f = Fetcher(registry, tmp_path / "snapshots", sleeper=sleeps.append)
    yield f
    # 防止真实网络调用漏网
    monkeypatch.undo()


def _install_ok_response(monkeypatch, captured=None, response=None):
    def fake_http_get(url, timeout_seconds):
        if captured is not None:
            captured.append({"url": url, "timeout": timeout_seconds})
        return response or FakeResponse()

    monkeypatch.setattr(fetcher_mod, "http_get", fake_http_get)


# ---------------------------------------------------------------------------
# Registry allowlist
# ---------------------------------------------------------------------------
class TestRegistryAllowlist:
    def test_registry_loads_and_has_gov_cn(self, registry):
        assert registry.enabled_sources, "至少一个 enabled 官方源"
        gov = [s for s in registry.enabled_sources if "gov.cn" in s.allowed_domains]
        assert gov, "第一阶段必须配置 gov.cn"

    def test_whitelisted_url_passes(self, registry):
        allowed, reason = registry.is_url_allowed(GOV_URL)
        assert allowed, reason

    def test_non_whitelisted_domain_rejected(self, registry):
        allowed, reason = registry.is_url_allowed("https://example.com/policy")
        assert not allowed
        assert "白名单" in reason

    def test_scheme_restriction(self, registry):
        for url in ("ftp://www.gov.cn/x", "file:///etc/passwd", "javascript:alert(1)"):
            allowed, reason = registry.is_url_allowed(url)
            assert not allowed, url
            assert "HTTP/HTTPS" in reason

    def test_registry_外_url_被_fetcher_拒绝且记录(self, fetcher, tmp_path):
        result = fetcher.fetch("https://example.com/policy.html")
        assert result.status == "failure"
        assert result.failure_type == "url_not_allowed"
        assert result.attempts == 0
        assert result.snapshot_ref is None
        # 失败必须留痕
        log = (tmp_path / "snapshots" / "fetch_failures.jsonl").read_text(encoding="utf-8")
        assert "url_not_allowed" in log

    def test_disabled_source_仍拒绝(self, tmp_path):
        reg_file = tmp_path / "reg.json"
        reg_file.write_text(json.dumps({
            "schema_version": "source-registry-v1",
            "rules": {"allow_new_domains_automatically": False},
            "sources": [{
                "source_id": "disabled_src", "organization": "x",
                "list_url": "https://disabled.example.gov.cn/list",
                "allowed_domains": ["disabled.example.gov.cn"],
                "enabled": False, "fetch_policy": {},
            }],
        }), encoding="utf-8")
        reg = SourceRegistry.from_file(reg_file)
        allowed, _ = reg.is_url_allowed("https://disabled.example.gov.cn/doc.html")
        assert not allowed, "disabled 源的域名也必须在白名单之外"

    def test_fail_closed_on_missing_registry(self, tmp_path):
        with pytest.raises(RegistryError):
            SourceRegistry.from_file(tmp_path / "nope.json")

    def test_fail_closed_on_bad_list_url_domain(self, tmp_path):
        reg_file = tmp_path / "reg.json"
        reg_file.write_text(json.dumps({
            "schema_version": "source-registry-v1",
            "sources": [{
                "source_id": "bad", "organization": "x",
                "list_url": "https://evil.com/list",
                "allowed_domains": ["gov.cn"],
                "enabled": True, "fetch_policy": {},
            }],
        }), encoding="utf-8")
        with pytest.raises(RegistryError):
            SourceRegistry.from_file(reg_file)


# ---------------------------------------------------------------------------
# Fetcher behavior
# ---------------------------------------------------------------------------
class TestFetcherBehavior:
    def test_user_agent_is_openinvest(self, fetcher, monkeypatch):
        seen = {}
        def capture_get(url, timeout=None, headers=None, **kw):
            seen.update(headers or {})
            return FakeResponse()
        monkeypatch.setattr(fetcher_mod.requests, "get", capture_get)
        fetcher_mod.http_get(GOV_URL, 20)
        assert seen.get("User-Agent") == "OpenInvest-PolicyResearch/1.0"
        assert "Mozilla" not in json.dumps(seen), "不得伪装浏览器指纹"

    def test_timeout_failure(self, fetcher, monkeypatch):
        def fake_get(url, timeout_seconds):
            raise requests.Timeout("timed out")
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        result = fetcher.fetch(GOV_URL)
        assert result.status == "failure"
        assert result.failure_type == "timeout"
        assert result.attempts == 3  # 有限重试上限
        assert result.snapshot_ref is None

    def test_connection_error_retry_cap(self, fetcher, monkeypatch):
        calls = []
        def fake_get(url, timeout_seconds):
            calls.append(url)
            raise requests.ConnectionError("refused")
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        result = fetcher.fetch(GOV_URL)
        assert result.failure_type == "connection_error"
        assert len(calls) == result.attempts == 3

    def test_http_4xx_no_retry(self, fetcher, monkeypatch):
        calls = []
        def fake_get(url, timeout_seconds):
            calls.append(url)
            return FakeResponse(status_code=404)
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        result = fetcher.fetch(GOV_URL)
        assert result.failure_type == "http_4xx"
        assert len(calls) == 1  # 4xx 不重试
        assert result.http_status == 404

    def test_http_5xx_retries_then_recovers(self, fetcher, monkeypatch):
        seq = [FakeResponse(status_code=500), FakeResponse(status_code=502), FakeResponse()]
        def fake_get(url, timeout_seconds):
            return seq.pop(0)
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        result = fetcher.fetch(GOV_URL)
        assert result.status == "ok"
        assert result.attempts == 3

    def test_unexpected_content_type(self, fetcher, monkeypatch):
        _install_ok_response(monkeypatch, None, FakeResponse(
            status_code=200, content=b"{}", headers={"Content-Type": "application/json"}))
        result = fetcher.fetch(GOV_URL)
        assert result.status == "failure"
        assert result.failure_type == "unexpected_content"
        assert result.snapshot_ref is None


# ---------------------------------------------------------------------------
# Snapshot behavior
# ---------------------------------------------------------------------------
class TestSnapshotBehavior:
    def test_snapshot_created_and_hash_correct(self, fetcher, monkeypatch, tmp_path):
        _install_ok_response(monkeypatch, None)
        result = fetcher.fetch(GOV_URL)
        assert result.status == "ok"
        snap = fetcher.snapshots_dir / result.snapshot_ref.removeprefix("snapshots/")
        assert snap.exists()
        assert snap.read_bytes() == SAMPLE_HTML  # raw 原样保存
        expected = __import__("hashlib").sha256(
            normalize_content(SAMPLE_HTML).encode("utf-8")).hexdigest()
        assert result.content_hash == expected

    def test_same_content_hash_deduped(self, fetcher, monkeypatch):
        seen_urls = []
        def fake_get(url, timeout_seconds):
            seen_urls.append(url)
            return FakeResponse(content=SAMPLE_HTML)
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        r1 = fetcher.fetch(GOV_URL)
        url2 = "https://www.gov.cn/zhengce/zhengceku/2017/content_5211996.htm"
        r2 = fetcher.fetch(url2)
        assert r1.content_hash == r2.content_hash
        assert r1.snapshot_ref == r2.snapshot_ref
        assert r1.snapshot_deduped is False
        assert r2.snapshot_deduped is True
        files = [p for p in fetcher.snapshots_dir.rglob("*") if p.is_file() and p.suffix != ".jsonl"]
        assert len(files) == 1  # 唯一 snapshot 文件

    def test_retrieved_at_is_utc(self, fetcher, monkeypatch):
        _install_ok_response(monkeypatch, None)
        result = fetcher.fetch(GOV_URL)
        ts = datetime.fromisoformat(result.retrieved_at)
        assert ts.tzinfo is not None and ts.utcoffset().total_seconds() == 0

    def test_default_snapshots_dir_is_production_path(self, registry):
        # 不传 snapshots_dir 时，必须落位到唯一生产路径（调用方不得自行发明）。
        f = Fetcher(registry)
        expected = fetcher_mod.DEFAULT_SNAPSHOTS_DIR
        assert f.snapshots_dir == expected
        assert expected.relative_to(REPO_ROOT).as_posix() == "data/raw_policies/snapshots"

    def test_low_frequency_interval_respected(self, registry, tmp_path, monkeypatch):
        sleeps = []
        f = Fetcher(registry, tmp_path / "s", sleeper=sleeps.append)
        # 预置 last_fetch 时间为刚刚 → 必须等待 min_interval
        import time as _time
        f._last_fetch_monotonic["www.gov.cn"] = _time.monotonic()
        # 取该源实际配置的低频 interval（不硬编码、不降低）
        src = f.registry.find_source_for_url(GOV_URL)
        min_interval = float(src.fetch_policy["min_interval_seconds"])
        _install_ok_response(monkeypatch, None)
        f.fetch(GOV_URL)
        # 实现保证两次同 host 抓取之间间隔 ≈ min_interval；sleep 时长因已流逝时间
        # 在 float 精度内可能略小于 min_interval，故用 1e-3 容差判定“至少达到低频”。
        assert any(s >= min_interval - 1e-3 for s in sleeps), (
            f"应等待 min_interval_seconds(={min_interval}), 实际 sleeps={sleeps}")


# ---------------------------------------------------------------------------
# Failure honesty
# ---------------------------------------------------------------------------
class TestFailureHonesty:
    def test_failure_produces_no_policy_no_snapshot(self, fetcher, monkeypatch, tmp_path):
        def fake_get(url, timeout_seconds):
            raise requests.Timeout("t")
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        result = fetcher.fetch(GOV_URL)
        assert result.status == "failure"
        assert result.content_hash is None and result.snapshot_ref is None
        # 无 snapshot 文件产生（除 failure log 外）
        snaps = [p for p in fetcher.snapshots_dir.rglob("*")
                 if p.is_file() and p.name != "fetch_failures.jsonl"]
        assert snaps == []

    def test_failure_log_records_reason(self, fetcher, monkeypatch, tmp_path):
        def fake_get(url, timeout_seconds):
            return FakeResponse(status_code=503)
        monkeypatch.setattr(fetcher_mod, "http_get", fake_get)
        fetcher.fetch(GOV_URL)
        log_path = tmp_path / "snapshots" / "fetch_failures.jsonl"
        record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
        assert record["failure_type"] == "http_5xx"
        assert record["error_message"] == "HTTP 503"
        assert record["url"] == GOV_URL


# ---------------------------------------------------------------------------
# Governance / Trust isolation
# ---------------------------------------------------------------------------
class TestGovernanceBoundary:
    def test_snapshots_gitignored(self):
        proc = subprocess.run(
            ["git", "check-ignore", "data/raw_policies/snapshots/probe.html"],
            cwd=REPO_ROOT, capture_output=True)
        assert proc.returncode == 0, "data/raw_policies/snapshots/ 必须被 gitignore"

    def test_no_trust_imports(self):
        for f in ("source_registry.py", "fetcher.py", "__init__.py"):
            src = (REPO_ROOT / "global_policy_aggregator" / "pipeline" / f).read_text(encoding="utf-8")
            import_lines = [l.strip() for l in src.splitlines()
                            if l.strip().startswith(("import ", "from ")) and "trust" in l.lower()]
            assert not import_lines, f"{f} 不得 import src/trust: {import_lines}"

    def test_no_verified_no_verification_status(self):
        import dataclasses
        # 运行时断言：FetchResult 信封不含任何核验语义字段
        field_names = {f.name for f in dataclasses.fields(fetcher_mod.FetchResult)}
        assert not any("verification" in n for n in field_names), field_names
        assert not any("VERIF" in n for n in dir(fetcher_mod)), "模块命名空间不得出现核验常量"
        # 静态断言：源码不含核验状态写入路径
        for f in ("source_registry.py", "fetcher.py"):
            src = (REPO_ROOT / "global_policy_aggregator" / "pipeline" / f).read_text(encoding="utf-8")
            assert "verification_status" not in src, f"{f} 不得出现 verification_status"
            assert "VERIFIED" not in src, f"{f} 不得出现 VERIFIED"
            assert "is_mock" not in src, f"{f} 不得出现 is_mock"

    def test_no_real_policies_writes(self):
        src = (REPO_ROOT / "global_policy_aggregator" / "pipeline" / "fetcher.py").read_text(encoding="utf-8")
        assert "real_policies.json" not in src, "fetcher 不得写 real_policies.json"
        # 运行时断言：成功/失败结果都不携带任何 policy 数据
        result = fetcher_mod.FetchResult.failure("https://www.gov.cn/x", "http_4xx", "HTTP 404", attempts=1)
        assert not any("policy" in k for k in result.to_dict())

    def test_existing_20_real_policies_contract_intact(self):
        data = json.loads((REPO_ROOT / "global_policy_aggregator" / "data" / "real_policies" /
                           "real_policies.json").read_text(encoding="utf-8"))
        assert len(data) == 20
        assert [p["id"] for p in data] == list(range(101, 121))
        for p in data:
            assert p["is_mock"] is False
            assert p["verification_status"] == "unverified"
            assert p["source_url"].startswith(("http://", "https://"))
