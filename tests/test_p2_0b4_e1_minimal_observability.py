"""P2-0B.4: E1 Minimal Observability tests.

验证最小真实 E1 观测链（Policy -> Project Intent Demand Signal）：
- 断点 A：首页搜索 beacon（POST /api/event/search）-> POLICY_SEARCHED（不记 keywords）
- 断点 B：POST /api/project-intent -> PROJECT_INTENT record + PROJECT_INTENT_CREATED event
- Regression：B.3 的 POLICY_SEARCHED / POLICY_VIEWED 路径继续正常工作

ProjectIntent != Project：不产生 Project / Claim / Match record。
actor_id 为实验匿名标识（anonymous_*），不伪造真实用户身份。
所有测试使用 tmp_path 隔离 store，绝不写真实 p2_0_experimental/records/ 目录。
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
MODULE_NAME = "p2_0b4_portal_under_test"


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


class TestSearchBeacon:
    def test_beacon_returns_ok_and_records_policy_searched(self, portal):
        _, store, client = portal
        resp = client.post("/api/event/search")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["record_type"] == "EVENT"
        assert ev["event_type"] == "POLICY_SEARCHED"
        assert ev["source"] == "interactive_ai_server"
        assert ev["object_type"] is None
        assert ev["object_id"] is None

    def test_beacon_event_passes_validator_with_canonical_id(self, portal):
        from p2_0_experimental.record_validator import compute_event_id, validate_event
        _, store, client = portal
        client.post("/api/event/search")
        events = store.read_all("EVENT")
        assert len(events) == 1
        ok, errors = validate_event(events[0])
        assert ok, errors
        assert events[0]["event_id"] == compute_event_id(events[0])

    def test_beacon_event_readable_from_isolated_jsonl_file(self, portal):
        _, store, client = portal
        client.post("/api/event/search")
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert store.read_by_id("EVENT", ev["event_id"]) == ev
        raw = (Path(store.records_dir) / "events.jsonl").read_text(encoding="utf-8")
        assert json.loads(raw.strip())["event_id"] == ev["event_id"]

    def test_beacon_ignores_keywords_no_keyword_recorded(self, portal):
        _, store, client = portal
        resp = client.post("/api/event/search", json={"keyword": "补贴", "query": "冷链物流"})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert set(ev.keys()) == {
            "record_type",
            "event_type",
            "timestamp",
            "source",
            "object_type",
            "object_id",
            "event_id",
        }
        assert "actor_id" not in ev
        raw = (Path(store.records_dir) / "events.jsonl").read_text(encoding="utf-8")
        assert "补贴" not in raw
        assert "冷链物流" not in raw
        assert "keyword" not in raw

    def test_beacon_logging_failure_does_not_break_http(self, portal, monkeypatch, capsys):
        module, store, client = portal

        def _boom():
            raise RuntimeError("store unavailable")

        monkeypatch.setattr(module, "_get_p2_0_store", _boom)
        resp = client.post("/api/event/search")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        assert "event logging failed" in capsys.readouterr().err

    def test_homepage_contains_beacon_and_need_ui_wiring(self, portal):
        _, _, client = portal
        resp = client.get("/")
        assert resp.status_code == 200
        assert "/api/event/search" in resp.text
        assert "/api/project-intent" in resp.text
        assert "submitProjectNeed" in resp.text
        assert "need-input-" in resp.text
        assert "function searchPolicies" in resp.text


class TestProjectIntent:
    def test_valid_intent_returns_ok_with_project_intent_id(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "想建设与该政策配套的冷链仓储项目"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["project_intent_id"]
        assert store.read_all("PROJECT_INTENT")

    def test_intent_record_created_and_passes_validator(self, portal):
        from p2_0_experimental.record_validator import validate_project_intent
        _, store, client = portal
        client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "想申报该政策支持的产业园区项目"},
        )
        records = store.read_all("PROJECT_INTENT")
        assert len(records) == 1
        rec = records[0]
        assert rec["record_type"] == "PROJECT_INTENT"
        assert rec["policy_id"] == "1"
        assert rec["need_description"] == "想申报该政策支持的产业园区项目"
        assert rec["source"] == "interactive_ai_server"
        assert rec["created_at"]
        ok, errors = validate_project_intent(rec)
        assert ok, errors

    def test_intent_created_event_passes_validator(self, portal):
        from p2_0_experimental.record_validator import validate_event
        _, store, client = portal
        client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "寻找该政策方向的项目合作机会"},
        )
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["record_type"] == "EVENT"
        assert ev["event_type"] == "PROJECT_INTENT_CREATED"
        assert ev["source"] == "interactive_ai_server"
        ok, errors = validate_event(ev)
        assert ok, errors

    def test_event_object_type_and_object_id_reference_intent(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "2", "need_description": "计划开展政策相关的设施改造"},
        )
        project_intent_id = resp.json()["project_intent_id"]
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["object_type"] == "PROJECT_INTENT"
        assert ev["object_id"] == project_intent_id
        rec = store.read_by_id("PROJECT_INTENT", project_intent_id)
        assert rec is not None
        assert rec["project_intent_id"] == project_intent_id

    def test_project_intent_id_is_uuid4(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "希望建设配套加工项目"},
        )
        project_intent_id = resp.json()["project_intent_id"]
        parsed = uuid.UUID(project_intent_id)
        assert parsed.version == 4
        assert str(parsed) == project_intent_id

    def test_policy_id_correctly_linked(self, portal):
        module, store, client = portal
        target = module.policies[3]["id"]
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": str(target), "need_description": "围绕该政策筹备种植基地项目"},
        )
        assert resp.json()["ok"] is True
        rec = store.read_all("PROJECT_INTENT")[0]
        assert rec["policy_id"] == str(target)

    def test_actor_consistent_between_record_and_event_and_anonymous(self, portal):
        _, store, client = portal
        client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "寻找政策资金支持的项目方向"},
        )
        rec = store.read_all("PROJECT_INTENT")[0]
        ev = store.read_all("EVENT")[0]
        assert rec["actor_id"]
        assert ev["actor_id"] == rec["actor_id"]
        assert rec["actor_id"].startswith("anonymous_")
        suffix = rec["actor_id"][len("anonymous_"):]
        assert len(suffix) == 12
        int(suffix, 16)

    def test_invalid_policy_id_rejected_no_records(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "999999", "need_description": "不存在政策的项目需求"},
        )
        assert resp.status_code == 200
        assert resp.json().get("error") == "Policy not found"
        assert store.read_all("PROJECT_INTENT") == []
        assert store.read_all("EVENT") == []

    def test_empty_need_description_rejected(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": ""},
        )
        assert resp.json().get("error") is not None
        assert store.read_all("PROJECT_INTENT") == []
        assert store.read_all("EVENT") == []

    def test_whitespace_only_need_description_rejected(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "   \n\t  "},
        )
        assert resp.json().get("error") is not None
        assert store.read_all("PROJECT_INTENT") == []
        assert store.read_all("EVENT") == []

    def test_malformed_json_body_rejected(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/project-intent",
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json().get("error") is not None
        assert store.read_all("PROJECT_INTENT") == []
        assert store.read_all("EVENT") == []

    def test_no_project_claim_match_records_created(self, portal):
        _, store, client = portal
        client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "希望建设农产品加工项目"},
        )
        found_types = set()
        for path in Path(store.records_dir).glob("*.jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    found_types.add(json.loads(line)["record_type"])
        assert found_types == {"EVENT", "PROJECT_INTENT"}
        assert found_types.isdisjoint({"PROJECT", "CLAIM", "MATCH", "HOOK", "PARTICIPANT", "POLICY"})

    def test_store_failure_does_not_pollute_records(self, portal, monkeypatch, capsys):
        _, store, client = portal

        def _boom(record):
            raise RuntimeError("disk full")

        monkeypatch.setattr(store, "append", _boom)
        resp = client.post(
            "/api/project-intent",
            json={"policy_id": "1", "need_description": "存储失败场景的项目需求"},
        )
        assert resp.status_code == 200
        assert resp.json().get("error") is not None
        assert store.read_all("PROJECT_INTENT") == []
        assert store.read_all("EVENT") == []
        assert "project intent record failed" in capsys.readouterr().err


class TestRegressionB3Continuity:
    def test_b3_api_search_still_works_shape_unchanged_no_actor(self, portal):
        module, store, client = portal
        resp = client.post("/api/search", json={"keywords": "", "limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"count", "policies"}
        assert data["count"] == len(module.policies)
        assert len(data["policies"]) == 3
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "POLICY_SEARCHED"
        assert set(ev.keys()) == {
            "record_type",
            "event_type",
            "timestamp",
            "source",
            "object_type",
            "object_id",
            "event_id",
        }
        assert "actor_id" not in ev

    def test_b3_pdf_view_still_logs_policy_viewed(self, portal):
        module, store, client = portal
        policy_id = module.policies[0]["id"]
        resp = client.get(f"/api/policy/{policy_id}/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/pdf")
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "POLICY_VIEWED"
        assert ev["object_type"] == "POLICY"
        assert ev["object_id"] == str(policy_id)

    def test_full_e1_chain_events_in_order(self, portal):
        module, store, client = portal
        client.post("/api/event/search")
        policy_id = module.policies[0]["id"]
        client.get(f"/api/policy/{policy_id}/pdf")
        client.post(
            "/api/project-intent",
            json={"policy_id": str(policy_id), "need_description": "端到端链路验证的项目需求"},
        )
        events = store.read_all("EVENT")
        assert [e["event_type"] for e in events] == [
            "POLICY_SEARCHED",
            "POLICY_VIEWED",
            "PROJECT_INTENT_CREATED",
        ]
        records = store.read_all("PROJECT_INTENT")
        assert len(records) == 1
        assert records[0]["policy_id"] == str(policy_id)
        assert events[2]["object_id"] == records[0]["project_intent_id"]
        assert events[2]["actor_id"] == records[0]["actor_id"]

    def test_homepage_still_200_with_search_intact(self, portal):
        _, _, client = portal
        resp = client.get("/")
        assert resp.status_code == 200
        assert "OpenInvest" in resp.text
        assert "function searchPolicies" in resp.text
