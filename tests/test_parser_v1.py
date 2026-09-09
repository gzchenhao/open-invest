"""P3-2 Parser 测试：HTML → ParsedContent，fail-safe / 结构变化 / 解析失败。"""

from pathlib import Path

from global_policy_aggregator.pipeline import parser as P
from global_policy_aggregator.pipeline.parser import (
    ParseError,
    ParseFailure,
    parse_html,
)
from global_policy_aggregator.pipeline.normalizer import run_pipeline

FIX = Path(__file__).resolve().parent / "fixtures" / "pipeline"
SRC = "https://www.gov.cn/policy/example.html"
SNAP = "snapshots/example/abc.html"


def load(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_parse_normal():
    pc = parse_html(load("fixture_normal.html"), SRC, SNAP)
    assert pc.clean_text.strip()
    assert pc.title_raw and "深圳市人工智能产业发展规划" in pc.title_raw
    assert pc.h1_raw == "深圳市人工智能产业发展规划"
    assert pc.structure_changed is False
    assert pc.parser_backend == "lxml"


def test_parse_structure_changed_fallback():
    pc = parse_html(load("fixture_structure_changed.html"), SRC, SNAP)
    # 无 <main>/<article>/id|class 含 content|main → 回退 body，标记结构变化
    assert pc.structure_changed is True
    assert pc.clean_text.strip()
    assert "结构变化下的政策标题" in pc.clean_text


def test_parse_empty_content_raises():
    html = "<html><body><script>1</script><style>x</style></body></html>"
    try:
        parse_html(html, SRC, SNAP)
        assert False, "expected ParseError(empty_content)"
    except ParseError as e:
        assert e.failure_type == "empty_content"


def test_parse_none_raises_parse_error():
    try:
        parse_html(None, SRC, SNAP)
        assert False, "expected ParseError(parse_error)"
    except ParseError as e:
        assert e.failure_type == "parse_error"


def test_parse_garbled_no_crash():
    pc = parse_html(load("fixture_garbled.html"), SRC, SNAP)
    assert isinstance(pc, P.ParsedContent)
    assert pc.clean_text is not None


def test_run_pipeline_returns_candidate_on_success():
    res = run_pipeline(load("fixture_normal.html"), SRC, SNAP)
    assert not isinstance(res, ParseFailure)
    assert res.title == "深圳市人工智能产业发展规划"


def test_run_pipeline_returns_parse_failure_on_empty():
    res = run_pipeline(
        "<html><body><script>1</script></body></html>", SRC, SNAP)
    assert isinstance(res, ParseFailure)
    assert res.failure_type == "empty_content"
