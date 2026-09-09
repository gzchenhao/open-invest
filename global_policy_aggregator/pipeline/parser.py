"""P3-2 HTML parser — Snapshot → ParsedContent。

设计纪律（JUDGE 最终决策）：
- 使用已有 ``bs4`` + ``lxml``（已在 requirements.txt，不新增依赖）。
- 不使用 headless browser、不依赖真实网络、不恢复旧 crawler 架构。
- 流程：BeautifulSoup/lxml → 去除 nav/script/style/header/footer 等噪声 →
  clean text + landmark（<title> / <h1>）。
- fail-safe：HTML 无法解析 / 正文为空 / 结构变化回退到 raw text，均 typed 处理，
  绝不硬猜。"看起完整"的 Candidate 不会在解析失败时产生。
"""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

PARSER_BACKEND = "lxml"

# 解析失败时写入的 runtime artifact（gitignored，绝不进 Git）。
DEFAULT_RAW_POLICIES_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "raw_policies"
)


class ParseError(Exception):
    """解析失败（typed）。由调用方转换为 ParseFailure 或自行处理。"""

    def __init__(self, failure_type: str, detail: str,
                 source_url: Optional[str] = None,
                 snapshot_ref: Optional[str] = None):
        self.failure_type = failure_type      # parse_error | empty_content | structure_changed
        self.detail = detail
        self.source_url = source_url
        self.snapshot_ref = snapshot_ref
        super().__init__(f"[{failure_type}] {detail}")


@dataclass
class ParseFailure:
    failure_type: str
    source_url: Optional[str]
    snapshot_ref: Optional[str]
    detail: str
    detected_at: str
    parser_backend: str = PARSER_BACKEND

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ParsedContent:
    source_url: str
    snapshot_ref: Optional[str]
    clean_text: str
    title_raw: Optional[str] = None
    h1_raw: Optional[str] = None
    meta: dict = field(default_factory=dict)
    structure_changed: bool = False           # 是否触发了结构变化回退
    parser_backend: str = PARSER_BACKEND

    def to_dict(self) -> dict:
        return asdict(self)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_ws(text: str) -> str:
    """折叠空白：多空格→单空格，去首尾空白。"""
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def parse_html(html: str, source_url: str, snapshot_ref: Optional[str] = None) -> ParsedContent:
    """将官方源 HTML 解析为 ParsedContent。

    Raises:
        ParseError: 解析失败（parse_error / empty_content / structure_changed）。
    """
    if html is None:
        raise ParseError("parse_error", "html is None", source_url, snapshot_ref)
    try:
        soup = BeautifulSoup(html, PARSER_BACKEND)
    except Exception as exc:  # bs4/lxml 底层异常
        raise ParseError("parse_error", f"BeautifulSoup failed: {exc}", source_url, snapshot_ref) from exc

    # 去噪声标签
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "noscript", "iframe", "form", "svg"]):
        tag.decompose()

    title_raw = soup.title.get_text(strip=True) if soup.title else None
    h1 = soup.find("h1")
    h1_raw = h1.get_text(strip=True) if h1 else None

    # 优先主内容 landmark；缺失则回退到 body（标记结构变化）。
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"content|main|article", re.I))
        or soup.find(class_=re.compile(r"content|main|article", re.I))
    )
    structure_changed = False
    if main:
        body_text = main.get_text("\n")
    else:
        body = soup.body or soup
        body_text = body.get_text("\n")
        structure_changed = True

    clean_text = _clean_ws(body_text)
    if not clean_text.strip():
        raise ParseError("empty_content", "正文为空（解析后无可见文本）", source_url, snapshot_ref)

    return ParsedContent(
        source_url=source_url,
        snapshot_ref=snapshot_ref,
        clean_text=clean_text,
        title_raw=title_raw,
        h1_raw=h1_raw,
        structure_changed=structure_changed,
    )


def record_parse_failure(pf: ParseFailure, failures_dir: Optional[str] = None) -> Path:
    """将 ParseFailure 追加写入 parse_failures.jsonl（runtime artifact）。"""
    root = Path(failures_dir) if failures_dir else DEFAULT_RAW_POLICIES_DIR
    path = root / "parse_failures.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(pf.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return path
