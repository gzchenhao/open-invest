"""P3-1 Fetcher + Snapshot — Pipeline 的 FETCH 阶段（P3-0 契约，JUDGE 批准）。

行为边界：
- 仅 HTTP/HTTPS，域名必须在 source registry 白名单内（registry 外 URL 一律拒绝）。
- User-Agent 明确标识 OpenInvest-PolicyResearch/1.0；不伪装浏览器指纹、不绕 WAF、
  不使用 headless browser、不做 aggressive crawling（低频 + per-host 间隔 + 有限重试）。
- 成功 → 保存 raw snapshot（runtime artifact，不进 Git）+ 规范化正文 SHA-256（按 hash 去重）。
- 失败 → 如实记录 failure log（timeout / connection_error / http_4xx / http_5xx /
  unexpected_content / url_not_allowed）；不生成 policy、不伪装成功。
- 本模块不是 verification engine：不产生任何核验状态、不写任何核验标记、
  不 import src/trust/**、不触碰 REAL 政策数据文件（Portal 数据契约零接触）。
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from global_policy_aggregator.pipeline.source_registry import SourceRegistry

USER_AGENT = "OpenInvest-PolicyResearch/1.0"

# 生产环境唯一权威 snapshot 根目录；调用方不得自行发明其它生产路径。
# 测试通过传参注入临时目录以隔离 runtime artifact。
DEFAULT_SNAPSHOTS_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "raw_policies" / "snapshots"
)

# 失败类型（JUDGE 六分类；parse 相关失败不在本 Quest 范围）
FAILURE_TIMEOUT = "timeout"
FAILURE_CONNECTION = "connection_error"
FAILURE_HTTP_4XX = "http_4xx"
FAILURE_HTTP_5XX = "http_5xx"
FAILURE_UNEXPECTED_CONTENT = "unexpected_content"
FAILURE_NOT_ALLOWED = "url_not_allowed"

ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")

DEFAULT_FETCH_POLICY = {
    "timeout_seconds": 20,
    "max_attempts": 3,
    "min_interval_seconds": 3,
    "retry_backoff_seconds": 1.0,
}

# 非重试失败（重试无意义或被禁止）
_FINAL_FAILURES = {FAILURE_HTTP_4XX, FAILURE_UNEXPECTED_CONTENT, FAILURE_NOT_ALLOWED}


def normalize_content(raw_bytes: bytes) -> str:
    """规范化原始内容（UTF-8 解码、去 BOM、统一换行、去首尾空白），作为 content_hash 基准。"""
    text = raw_bytes.decode("utf-8", errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def compute_content_hash(raw_bytes: bytes) -> str:
    return hashlib.sha256(normalize_content(raw_bytes).encode("utf-8")).hexdigest()


def http_get(url: str, timeout_seconds: float):
    """HTTP 调用注入点（测试 monkeypatch 此函数，CI 不做真实网络请求）。"""
    return requests.get(
        url,
        timeout=timeout_seconds,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html, application/xhtml+xml, text/plain",
        },
        allow_redirects=True,
    )


@dataclass
class FetchResult:
    url: str
    status: str                      # "ok" | "failure"
    failure_type: str | None         # FAILURE_* 之一（成功为 None）
    http_status: int | None
    attempts: int
    source_id: str | None
    retrieved_at: str | None         # UTC ISO8601，成功时必有
    content_hash: str | None
    snapshot_ref: str | None
    snapshot_deduped: bool
    size_bytes: int | None
    error_message: str | None

    @classmethod
    def failure(cls, url, failure_type, error_message, attempts, source_id=None, http_status=None):
        return cls(
            url=url, status="failure", failure_type=failure_type,
            http_status=http_status, attempts=attempts, source_id=source_id,
            retrieved_at=None, content_hash=None, snapshot_ref=None,
            snapshot_deduped=False, size_bytes=None, error_message=error_message,
        )

    def to_dict(self) -> dict:
        return asdict(self)


class Fetcher:
    """低频、可注入的官方源抓取器。snapshots_dir 下的所有内容均为 runtime artifact。"""

    def __init__(self, registry: SourceRegistry, snapshots_dir=None, sleeper=time.sleep):
        if not isinstance(registry, SourceRegistry):
            raise TypeError("registry 必须是 SourceRegistry")
        self.registry = registry
        # 生产默认使用唯一权威目录；传 None 时落位到 DEFAULT_SNAPSHOTS_DIR，
        # 调用方无需（也不应）自行指定生产 snapshot 路径。
        self.snapshots_dir = Path(snapshots_dir) if snapshots_dir is not None else DEFAULT_SNAPSHOTS_DIR
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self._sleeper = sleeper
        self._last_fetch_monotonic = {}  # host -> monotonic time（per-host 低频控制）

    # ── failure log ────────────────────────────────────────────────
    @property
    def failure_log_path(self) -> Path:
        return self.snapshots_dir / "fetch_failures.jsonl"

    def _log_failure(self, result: FetchResult) -> None:
        record = result.to_dict()
        record["logged_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.failure_log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    # ── snapshot ───────────────────────────────────────────────────
    def _snapshot_path(self, url: str, content_hash: str, content_type: str) -> Path:
        host = urlparse(url).netloc.lower()
        safe_host = host.replace(":", "_")
        ext = ".html" if "html" in (content_type or "").lower() else ".txt"
        return self.snapshots_dir / safe_host / f"{content_hash}{ext}"

    def _save_snapshot(self, url, raw_bytes, content_hash, content_type):
        """按 content_hash 去重保存 raw 字节；返回 (snapshot_ref, deduped)。"""
        path = self._snapshot_path(url, content_hash, content_type)
        deduped = path.exists()
        if not deduped:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw_bytes)
        rel = path.relative_to(self.snapshots_dir).as_posix()
        return f"snapshots/{rel}", deduped

    # ── 低频控制 ───────────────────────────────────────────────────
    def _respect_interval(self, host: str, min_interval_seconds: float) -> None:
        elapsed = time.monotonic() - self._last_fetch_monotonic.get(host, 0.0)
        wait = min_interval_seconds - elapsed
        if wait > 0:
            self._sleeper(wait)
        self._last_fetch_monotonic[host] = time.monotonic()

    # ── 主入口 ─────────────────────────────────────────────────────
    def fetch(self, url: str) -> FetchResult:
        allowed, reason = self.registry.is_url_allowed(url)
        if not allowed:
            result = FetchResult.failure(url, FAILURE_NOT_ALLOWED, reason, attempts=0)
            self._log_failure(result)
            return result

        entry = self.registry.find_source_for_url(url)
        policy = dict(DEFAULT_FETCH_POLICY)
        if entry:
            policy.update(entry.fetch_policy)
            source_id = entry.source_id
        else:
            source_id = None

        host = urlparse(url).netloc.lower()
        self._respect_interval(host, float(policy.get("min_interval_seconds", 0)))

        attempts = 0
        failure_type = None
        error_message = None
        http_status = None

        while attempts < int(policy.get("max_attempts", 1)):
            attempts += 1
            try:
                response = http_get(url, float(policy.get("timeout_seconds", 20)))
            except requests.Timeout as exc:
                failure_type, error_message, http_status = FAILURE_TIMEOUT, str(exc), None
            except requests.RequestException as exc:
                failure_type, error_message, http_status = FAILURE_CONNECTION, str(exc), None
            else:
                http_status = response.status_code
                if 400 <= http_status < 500:
                    failure_type, error_message = FAILURE_HTTP_4XX, f"HTTP {http_status}"
                elif 500 <= http_status < 600:
                    failure_type, error_message = FAILURE_HTTP_5XX, f"HTTP {http_status}"
                else:
                    content_type = response.headers.get("Content-Type", "") or ""
                    raw_bytes = response.content or b""
                    if not any(ct in content_type.lower() for ct in ALLOWED_CONTENT_TYPES):
                        failure_type = FAILURE_UNEXPECTED_CONTENT
                        error_message = f"Content-Type 不被接受: {content_type or '(missing)'}"
                    elif len(raw_bytes) == 0:
                        failure_type = FAILURE_UNEXPECTED_CONTENT
                        error_message = "响应体为空"
                    else:
                        return self._finalize_success(url, raw_bytes, content_type, attempts, source_id, http_status)

            # 决定是否重试
            if failure_type in _FINAL_FAILURES or attempts >= int(policy.get("max_attempts", 1)):
                break
            self._sleeper(float(policy.get("retry_backoff_seconds", 0)))

        result = FetchResult.failure(url, failure_type, error_message, attempts, source_id, http_status)
        self._log_failure(result)
        return result

    def _finalize_success(self, url, raw_bytes, content_type, attempts, source_id, http_status) -> FetchResult:
        content_hash = compute_content_hash(raw_bytes)
        snapshot_ref, deduped = self._save_snapshot(url, raw_bytes, content_hash, content_type)
        return FetchResult(
            url=url, status="ok", failure_type=None, http_status=http_status,
            attempts=attempts, source_id=source_id,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            content_hash=content_hash, snapshot_ref=snapshot_ref,
            snapshot_deduped=deduped, size_bytes=len(raw_bytes), error_message=None,
        )
