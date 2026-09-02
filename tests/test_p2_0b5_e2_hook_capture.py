"""P2-0B.5: E2 Project Hook Capture tests.

验证最小 E2 conversion 链（ProjectIntent -> 用户独立动作 -> ProjectHook）：
- POST /api/project-hook：project_intent_id 必须真实存在（防 orphan Hook；不存在 -> 4xx）
- HOOK record 严格 6 字段（Hook != Claim / != Project / != Match，无状态机）
- PROJECT_HOOK_CREATED event：object_type=HOOK、object_id=hook_id、无 actor_id
- 绝不自动派生：POST /api/project-intent 单独不产生任何 Hook（E2 conversion 语义）
- 重复 HTTP 提交 = 独立 Hook（R4 裁决：frontend disable + backend no dedup）

MOCK policy 环境仅用于工程链路测试（ENGINEERING TEST ONLY），
不代表 authentic E2 evidence。所有测试使用 tmp_path 隔离 store，
绝不写真实 p2_0_experimental/records/ 目录。
注意：根 .gitignore 忽略 test_*.py，commit 时需 git add -f。
"""

import importlib.util
import json
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
MODULE_NAME = "p2_0b5_portal_under_test"

HOOK_KEYS = {"record_type", "hook_id", "hook_type", "object_id", "created_at", "source"}
FORBIDDEN_HOOK_KEYS = {
    "status", "claim_status", "claim_token", "claim_owner", "claim_verified",
    "metadata", "participant_id", "project_id", "match_score", "investment_id",
    "contact", "evidence_ref",
}


def _load_portal_module():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location(MODULE_NAME, PORTAL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def portal(tmp_path, monkeypatch):
    module = _load_portal_module()
    from p2_0_experimental.jsonl_store import ExperimentalJSONLStore
    store = ExperimentalJSONLStore(records_dir=str(tmp_path / "records"))
    monkeypatch.setattr(module, "_p2_0_store", store)
    client = TestClient(module.app)
    return module, store, client


def _create_intent(client, policy_id="1", need="我们需要一笔研发补贴扩建产线"):
    resp = client.post(
        "/api/project-intent",
        json={"policy_id": policy_id, "need_description": need},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    return data["project_intent_id"]


class TestHookCapture:
    def test_t1_valid_intent_creates_hook_record(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        resp = client.post("/api/project-hook", json={"project_intent_id": pid})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        hooks = store.read_all("HOOK")
        assert len(hooks) == 1
        hook = hooks[0]
        assert hook["hook_id"] == data["hook_id"]
        assert uuid.UUID(hook["hook_id"]).version == 4

    def test_t2_unknown_intent_rejected_4xx_no_hook(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-hook", json={"project_intent_id": str(uuid.uuid4())}
        )
        assert 400 <= resp.status_code < 500
        assert "error" in resp.json()
        assert store.read_all("HOOK") == []

    def test_t3_hook_exact_six_field_shape(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        hook = store.read_all("HOOK")[0]
        assert set(hook.keys()) == HOOK_KEYS
        assert hook["record_type"] == "HOOK"
        assert hook["hook_type"] == "PROJECT_HOOK"
        for field in ("hook_id", "object_id", "created_at", "source"):
            assert isinstance(hook[field], str) and hook[field]
        for forbidden in FORBIDDEN_HOOK_KEYS:
            assert forbidden not in hook

    def test_t4_hook_passes_b2_validator(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        hook = store.read_all("HOOK")[0]
        from p2_0_experimental.record_validator import validate_hook
        ok, errors = validate_hook(hook)
        assert ok, errors

    def test_t5_project_hook_created_event_written(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        events = store.read_all("EVENT")
        created = [e for e in events if e["event_type"] == "PROJECT_HOOK_CREATED"]
        assert len(created) == 1
        assert created[0].get("event_id")

    def test_t6_event_object_points_to_hook_itself(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        resp = client.post("/api/project-hook", json={"project_intent_id": pid})
        hook_id = resp.json()["hook_id"]
        ev = next(
            e for e in store.read_all("EVENT")
            if e["event_type"] == "PROJECT_HOOK_CREATED"
        )
        assert ev["object_type"] == "HOOK"
        assert ev["object_id"] == hook_id

    def test_t7_hook_object_id_points_to_project_intent(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        hook = store.read_all("HOOK")[0]
        assert hook["object_id"] == pid
        assert store.read_by_id("PROJECT_INTENT", pid) is not None

    def test_t8_hook_created_event_has_no_actor_id(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        ev = next(
            e for e in store.read_all("EVENT")
            if e["event_type"] == "PROJECT_HOOK_CREATED"
        )
        assert "actor_id" not in ev


class TestNoClaimNoMatchNoProject:
    def test_t9_t10_t11_no_claim_no_match_no_project_records(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        # read_all 对未知类型抛 ValueError，因此直接扫描原始 JSONL 行
        record_types = set()
        for jf in Path(store.records_dir).glob("*.jsonl"):
            for line in jf.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record_types.add(json.loads(line)["record_type"])
        assert record_types == {"EVENT", "PROJECT_INTENT", "HOOK"}
        assert record_types.isdisjoint({"PROJECT", "CLAIM", "MATCH"})


class TestNoAutoDerivation:
    def test_project_intent_alone_creates_no_hook(self, portal):
        _, store, client = portal
        _create_intent(client)
        # PROJECT_INTENT_CREATED 绝不自动派生 PROJECT_HOOK_CREATED（E2 conversion 语义）
        assert store.read_all("HOOK") == []
        event_types = {e["event_type"] for e in store.read_all("EVENT")}
        assert "PROJECT_HOOK_CREATED" not in event_types

    def test_no_need_text_shortcut_creates_hook(self, portal):
        # need_description 非空也不会自动创建 Hook：必须有第二个独立 HTTP 动作
        _, store, client = portal
        _create_intent(client, need="非空需求描述")
        assert store.read_all("HOOK") == []


class TestInputValidation:
    def test_t12_missing_empty_and_malformed_intent_rejected(self, portal):
        _, store, client = portal
        # missing 字段
        resp = client.post("/api/project-hook", json={})
        assert 400 <= resp.status_code < 500
        # 空字符串 / 纯空白
        resp = client.post("/api/project-hook", json={"project_intent_id": "  "})
        assert 400 <= resp.status_code < 500
        # 非 JSON body
        resp = client.post(
            "/api/project-hook",
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )
        assert 400 <= resp.status_code < 500
        assert store.read_all("HOOK") == []

    def test_t13_intent_to_hook_relation_is_consistent(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        resp = client.post("/api/project-hook", json={"project_intent_id": pid})
        hook_id = resp.json()["hook_id"]
        intent = store.read_by_id("PROJECT_INTENT", pid)
        hook = store.read_by_id("HOOK", hook_id)
        ev = next(
            e for e in store.read_all("EVENT")
            if e["event_type"] == "PROJECT_HOOK_CREATED"
        )
        # intent -> hook -> event 链完整且指向一致
        assert intent["project_intent_id"] == hook["object_id"]
        assert hook["hook_id"] == ev["object_id"]
        assert ev["object_type"] == "HOOK"


class TestDuplicatePolicyR4:
    def test_t15_duplicate_submissions_form_independent_hooks(self, portal):
        _, store, client = portal
        pid = _create_intent(client)
        r1 = client.post("/api/project-hook", json={"project_intent_id": pid})
        r2 = client.post("/api/project-hook", json={"project_intent_id": pid})
        assert r1.status_code == 200
        assert r2.status_code == 200
        hooks = store.read_all("HOOK")
        # 后端不做 dedup：重复 HTTP 请求 = 独立 Hook（真实行为噪声，如实记录）
        assert len(hooks) == 2
        assert hooks[0]["hook_id"] != hooks[1]["hook_id"]
        created = [
            e for e in store.read_all("EVENT")
            if e["event_type"] == "PROJECT_HOOK_CREATED"
        ]
        assert len(created) == 2

    def test_t15b_ui_button_hidden_then_disabled_independent_action(self, portal):
        module, _, client = portal
        html = client.get("/").text
        # Hook 按钮初始隐藏（display: none），仅在 Intent 成功后由 showHookAction 显示
        assert 'id="hook-btn-${policy.id}"' in html
        assert "display: none" in html
        assert "showHookAction(" in html
        # 点击后立即 disable（frontend disable；backend no dedup 属 R4 裁决）
        assert "btn.disabled = true" in html
        # submitProjectNeed 与 exposeProjectHook 是两个独立函数 = 两个独立用户动作
        assert "function submitProjectNeed(" in html
        assert "function exposeProjectHook(" in html
        assert 'fetch(\'/api/project-hook\'' in html


class TestB4Regression:
    def test_t14_b4_project_intent_endpoint_shape_unchanged(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "B4 回归：需求描述"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert set(data.keys()) == {"ok", "project_intent_id"}
        intent = store.read_all("PROJECT_INTENT")[0]
        assert set(intent.keys()) == {
            "record_type", "project_intent_id", "policy_id",
            "need_description", "actor_id", "created_at", "source",
        }
        assert intent["actor_id"].startswith("anonymous_")

    def test_t14b_b3_search_beacon_still_works_no_actor(self, portal):
        _, store, client = portal
        resp = client.post("/api/event/search")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "POLICY_SEARCHED"
        assert ev["source"] == "interactive_ai_server"
        assert "actor_id" not in ev


class TestRecordsIsolation:
    def test_t16_records_isolated_from_production_dir(self, portal, tmp_path):
        module, store, client = portal
        pid = _create_intent(client)
        client.post("/api/project-hook", json={"project_intent_id": pid})
        # 生产目录保持 CLEAN：绝不出现 hooks.jsonl
        assert not (module._P2_0_RECORDS_DIR / "hooks.jsonl").exists()
        # tmp 隔离目录恰好三个 jsonl
        files = {p.name for p in Path(store.records_dir).glob("*.jsonl")}
        assert files == {"project_intents.jsonl", "hooks.jsonl", "events.jsonl"}
