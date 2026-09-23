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

# ── D1（P4-5.1）：提前闭合 </html>/</body> 的确定性恢复 ───────────────────
# 部分官方模板（例如 gov.cn zhengceku）在页头之后输出提前闭合的 </html>，
# lxml 会静默丢弃其后全部正文（只剩页头导航），且不抛异常。
# 恢复策略：若某次 </html>/</body> 之后仍存在结构化标记（证明文档在其后继续），
# 则该次闭合属于「提前闭合」，予以移除。该操作只删除闭合标签、绝不删除内容，
# 因此不会引入页面之外的内容；判定纯结构化，与具体 URL / 站点无关。
_EARLY_CLOSE_RE = re.compile(r"</\s*(?:html|body)\s*>", re.I)
_STRUCTURAL_TAG_RE = re.compile(
    r"<\s*(?:div|p|table|tr|td|th|section|article|main|ul|ol|li|span"
    r"|h[1-6]|br|img|a|pre|blockquote)\b",
    re.I,
)

# ── D1：正文完整性校验（fail-closed）─────────────────────────────────────
# 解析所得正文不得明显小于「原始可见文本」。仅在原始页面文本量足够时启用，
# 以免误伤短页面。
_MIN_RAW_TEXT_FOR_INTEGRITY = 400
_MIN_BODY_TEXT_RATIO = 0.10

# ── D2（P4-5.1）：正文 landmark 选择（token 精确匹配 + 歧义 fail-closed）─
# 旧实现用未锚定正则 ``content|main|article`` 做子串匹配，``class="mainnav"``
# 会命中 ``main``，于是把导航栏当成正文。改为「按分隔符切 token 后精确比对」。
_CONTENT_TOKENS = frozenset({
    "content", "main", "article", "articlebody", "mainbody", "contentbody",
    "contentbox", "document", "docbody", "post", "entry", "detail",
    "detailcontent",
})
_NAV_TOKENS = frozenset({
    "nav", "navbar", "navigation", "mainnav", "subnav", "topnav", "sidenav",
    "menu", "menubar", "breadcrumb", "breadcrumbs", "crumb", "crumbs",
    "header", "footer", "sidebar", "aside", "toolbar", "topbar", "bottombar",
    "search", "share", "related", "recommend", "copyright", "banner",
    "sitemap", "pagination", "pager", "comment", "comments",
})
# 多个「极大」正文候选共存时，最大者必须显著大于次大者才可确定性选取；
# 否则视为歧义 → ParseError（绝不凭「第一个匹配 main」猜测）。
_LANDMARK_DOMINANCE = 2.0

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


def _recover_early_closed_html(html: str):
    """确定性中和「提前闭合」的 </html> / </body>（D1）。

    仅当某次闭合之后仍存在结构化标记（证明文档在其后继续）时才移除该次闭合，
    因此对良构文档是无操作；且只删除闭合标签、绝不删除内容。

    Returns:
        (recovered_html, removed_count)
    """
    if not html:
        return html, 0
    parts, last, removed = [], 0, 0
    for m in _EARLY_CLOSE_RE.finditer(html):
        if _STRUCTURAL_TAG_RE.search(html, m.end()):
            parts.append(html[last:m.start()])
            last = m.end()
            removed += 1
    if not removed:
        return html, 0
    parts.append(html[last:])
    return "".join(parts), removed


def _raw_visible_text_len(html: str) -> int:
    """估算原始 HTML 的可见文本长度（去 script/style/标签/空白）。"""
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;|&#160;|&amp;|&lt;|&gt;|&quot;", " ", t)
    return len(re.sub(r"\s+", "", t))


def _attr_tokens(el) -> set:
    """把元素的 id/class 按非字母数字切分为 token 集合（精确匹配，不做子串）。"""
    raw = " ".join(filter(None, [el.get("id") or "",
                                 " ".join(el.get("class") or [])]))
    return {t for t in re.split(r"[^0-9a-zA-Z\u4e00-\u9fa5]+", raw.lower()) if t}


def _is_ancestor(ancestor, node) -> bool:
    return any(p is ancestor for p in node.parents)


def _select_landmark(soup):
    """确定性选择正文容器（D2）。

    Returns:
        (element | None, note)，note ∈ {main_tag, attr_content, body_fallback,
        ambiguous_body}
    """
    # 唯一 <main> 视为权威 landmark（与旧实现优先级一致），但落在导航容器内者除外。
    mains = [el for el in soup.find_all("main") if not (_attr_tokens(el) & _NAV_TOKENS)]
    if len(mains) == 1:
        return mains[0], "main_tag"

    cands = []
    for el in soup.find_all(True):
        if el.name in ("html", "body"):
            continue
        toks = _attr_tokens(el)
        if toks & _NAV_TOKENS:            # 导航/页脚/侧栏等绝不作为正文
            continue
        if toks & _CONTENT_TOKENS:
            cands.append(el)
    cands.extend(el for el in soup.find_all(["main", "article"])
                 if el not in cands and not (_attr_tokens(el) & _NAV_TOKENS))

    if not cands:
        return None, "body_fallback"

    # 只保留「极大」候选（剔除被其他候选包含者）
    maximal = [c for c in cands
               if not any(o is not c and _is_ancestor(o, c) for o in cands)]
    if len(maximal) == 1:
        return maximal[0], "attr_content"

    ranked = sorted(maximal, key=lambda e: len(e.get_text(" ", strip=True)),
                    reverse=True)
    top = len(ranked[0].get_text(" ", strip=True))
    second = len(ranked[1].get_text(" ", strip=True))
    if top > 0 and (second == 0 or top >= second * _LANDMARK_DOMINANCE):
        return ranked[0], "attr_content"
    return None, "ambiguous_body"


def parse_html(html: str, source_url: str, snapshot_ref: Optional[str] = None) -> ParsedContent:
    """将官方源 HTML 解析为 ParsedContent。

    Raises:
        ParseError: 解析失败（parse_error / empty_content / incomplete_body /
            ambiguous_body）。
    """
    if html is None:
        raise ParseError("parse_error", "html is None", source_url, snapshot_ref)

    # D1: 先确定性恢复「提前闭合」的 </html> / </body>，
    #     否则 lxml 会静默丢弃其后正文且不报错。
    recovered_html, premature_closes = _recover_early_closed_html(html)

    try:
        soup = BeautifulSoup(recovered_html, PARSER_BACKEND)
    except Exception as exc:  # bs4/lxml 底层异常
        raise ParseError("parse_error", f"BeautifulSoup failed: {exc}", source_url, snapshot_ref) from exc

    # 去噪声标签
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "noscript", "iframe", "form", "svg"]):
        tag.decompose()

    title_raw = soup.title.get_text(strip=True) if soup.title else None
    h1 = soup.find("h1")
    h1_raw = h1.get_text(strip=True) if h1 else None

    # D2: 选择主内容 landmark；缺失则回退 body（结构变化）；歧义则 fail-closed。
    main, landmark_note = _select_landmark(soup)
    if landmark_note == "ambiguous_body":
        raise ParseError(
            "ambiguous_body",
            "存在多个同等量级的正文候选容器，无法确定性选择正文（fail-closed）",
            source_url, snapshot_ref,
        )

    structure_changed = False
    if main is not None:
        body_text = main.get_text("\n")
    else:
        body = soup.body or soup
        body_text = body.get_text("\n")
        structure_changed = True

    clean_text = _clean_ws(body_text)
    if not clean_text.strip():
        raise ParseError("empty_content", "正文为空（解析后无可见文本）", source_url, snapshot_ref)

    # D1: 完整性校验（fail-closed）——不得把「明显小于原始正文」的结果当作成功。
    raw_len = _raw_visible_text_len(recovered_html)
    clean_len = len(re.sub(r"\s+", "", clean_text))
    if raw_len >= _MIN_RAW_TEXT_FOR_INTEGRITY and clean_len < raw_len * _MIN_BODY_TEXT_RATIO:
        raise ParseError(
            "incomplete_body",
            f"正文完整性校验失败：clean_text={clean_len} 明显小于原始可见文本"
            f"={raw_len}（阈值 {_MIN_BODY_TEXT_RATIO:.0%}），拒绝产出伪完整政策",
            source_url, snapshot_ref,
        )

    return ParsedContent(
        source_url=source_url,
        snapshot_ref=snapshot_ref,
        clean_text=clean_text,
        title_raw=title_raw,
        h1_raw=h1_raw,
        meta={
            "landmark": landmark_note,
            "premature_closes_removed": premature_closes,
            "raw_visible_text_len": raw_len,
            "clean_text_len": clean_len,
        },
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
