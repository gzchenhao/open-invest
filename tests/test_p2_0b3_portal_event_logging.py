"""P2-0B.3: Portal Minimal Event Logging tests.

验证 interactive_ai_server 的真实行为正确产生 P2-0 实验事件：
- POST /api/search -> POLICY_SEARCHED
- GET /api/policy/{id}/pdf (found)     -> POLICY_VIEWED
- GET /api/policy/{id}/pdf (not found) -> 无事件
所有测试使用 tmp_path 隔离 store，绝不写真实 p2_0_experimental/records/ 目录。
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
MODULE_NAME = "p2_0b3_portal_under_test"


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


class TestPolicySearched:
    def test_search_api_writes_policy_searched_event(self, portal):
        _, store, client = portal
        resp = client.post("/api/search", json={"keywords": "补贴", "limit": 5})
        assert resp.status_code == 200
        events = store.read_all("EVENT")
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "POLICY_SEARCHED"
        assert ev["source"] == "interactive_ai_server"
        assert ev["object_type"] is None
        assert ev["object_id"] is None

    def test_search_event_passes_validator_with_canonical_id(self, portal):
        from p2_0_experimental.record_validator import compute_event_id, validate_event
        _, store, client = portal
        client.post("/api/search", json={"keywords": "demo"})
        events = store.read_all("EVENT")
        assert len(events) == 1
        ok, errors = validate_event(events[0])
        assert ok, errors
        assert events[0]["event_id"] == compute_event_id(events[0])

    def test_search_event_has_no_fabricated_actor(self, portal):
        _, store, client = portal
        client.post("/api/search", json={"keywords": ""})
        ev = store.read_all("EVENT")[0]
        assert ev.get("actor_id") is None
        assert ev.get("actor_type") is None

    def test_empty_keywords_search_still_records_event(self, portal):
        _, store, client = portal
        resp = client.post("/api/search", json={"keywords": "", "limit": 3})
        assert resp.status_code == 200
        events = store.read_all("EVENT")
        assert len(events) == 1
        assert events[0]["event_type"] == "POLICY_SEARCHED"

    def test_malformed_body_does_not_record_event(self, portal):
        _, store, client = portal
        resp = client.post(
            "/api/search",
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json().get("error") is not None
        assert store.read_all("EVENT") == []

    def test_search_then_view_produces_both_events_in_order(self, portal):
        module, store, client = portal
        client.post("/api/search", json={"keywords": ""})
        policy_id = module.policies[0]["id"]
        client.get(f"/api/policy/{policy_id}/pdf")
        events = store.read_all("EVENT")
        assert [e["event_type"] for e in events] == [
            "POLICY_SEARCHED",
            "POLICY_VIEWED",
        ]


class TestPolicyViewed:
    def test_pdf_found_writes_policy_viewed_event(self, portal):
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
        assert ev["source"] == "interactive_ai_server"

    def test_pdf_not_found_writes_no_event(self, portal):
        _, store, client = portal
        resp = client.get("/api/policy/999999/pdf")
        assert resp.status_code == 200
        assert resp.json() == {"error": "Policy not found"}
        assert store.read_all("EVENT") == []

    def test_viewed_event_passes_validator(self, portal):
        from p2_0_experimental.record_validator import validate_event
        module, store, client = portal
        policy_id = module.policies[0]["id"]
        client.get(f"/api/policy/{policy_id}/pdf")
        events = store.read_all("EVENT")
        assert len(events) == 1
        ok, errors = validate_event(events[0])
        assert ok, errors

    def test_two_downloads_of_different_policies_two_events(self, portal):
        module, store, client = portal
        id_a = module.policies[0]["id"]
        id_b = module.policies[1]["id"]
        client.get(f"/api/policy/{id_a}/pdf")
        client.get(f"/api/policy/{id_b}/pdf")
        events = store.read_all("EVENT")
        assert len(events) == 2
        assert {e["object_id"] for e in events} == {str(id_a), str(id_b)}


class TestApiBehaviorUnchanged:
    def test_search_response_shape_unchanged(self, portal):
        module, _, client = portal
        resp = client.post("/api/search", json={"keywords": "", "limit": 2})
        data = resp.json()
        assert set(data.keys()) == {"count", "policies"}
        assert data["count"] == len(module.policies)
        assert len(data["policies"]) == 2

    def test_homepage_still_200(self, portal):
        _, _, client = portal
        resp = client.get("/")
        assert resp.status_code == 200
        assert "OpenInvest" in resp.text

    def test_stats_endpoint_unaffected(self, portal):
        _, _, client = portal
        resp = client.get("/api/stats")
        assert resp.status_code == 200

    def test_logging_failure_does_not_break_api(self, portal, monkeypatch, capsys):
        module, _, client = portal

        def _boom():
            raise RuntimeError("store unavailable")

        monkeypatch.setattr(module, "_get_p2_0_store", _boom)
        resp = client.post("/api/search", json={"keywords": ""})
        assert resp.status_code == 200
        assert "count" in resp.json()
        assert "event logging failed" in capsys.readouterr().err

    def test_events_persist_to_isolated_jsonl_file(self, portal):
        _, store, client = portal
        client.post("/api/search", json={"keywords": ""})
        jsonl_files = list(Path(store.records_dir).glob("*.jsonl"))
        assert jsonl_files, "expected JSONL file under isolated records dir"
        assert store.read_all("EVENT")[0]["record_type"] == "EVENT"
