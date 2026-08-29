"""
P1-3.4 — ChinaPolicyCleaningService Runtime Integration Tests (F-10 Closure)

These tests exercise the REAL runtime path of ChinaPolicyCleaningService:

    raw policy text
        -> ChinaPolicyCleaningService (batch_clean_china_policies /
           _clean_china_policy_text)
        -> actual StructuredPolicy output
        -> canonical_industry

They do NOT call Registry.resolve() directly and assert on it (that layer
is already covered by P1-3.2/P1-3.3 tests). F-10 (P1-3.3.1 Independent
Verification) required exactly this coverage.

Scope notes (honesty constraints):
- The production ``china_industry_mapping`` is a LOCAL variable inside
  ``_extract_china_basic_info`` and can only emit 10 EN values plus the
  "other" fallback. Legacy keys such as ``ai_hardware`` or synonym /
  normalization / semantic keys are NOT reachable through the service's
  runtime path, so they CANNOT be honestly tested here (attempting to
  monkeypatch the instance attribute has no effect on the local mapping).
  Their canonical behavior is covered at registry level by P1-3.3 tests
  (tests/test_taxonomy_integration.py), and the ai_hardware -> UNKNOWN
  runtime proof is provided through the fixed_server seed path instead
  (see tests/test_fixed_server_runtime_integration.py).
- No real government data is used anywhere; all policy texts below are
  synthetic MOCK text.

Quest: P1-3.4 — Runtime Integration Test Closure (closes F-10)
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Ensure project root and aggregator package are importable
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
AGGREGATOR_ROOT = PROJECT_ROOT / "global_policy_aggregator"
if str(AGGREGATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(AGGREGATOR_ROOT))

# NOTE: the top-level name "services" is ambiguous in this repo:
#   server/services            -> regular package (has __init__.py)
#   global_policy_aggregator/services -> namespace package
# With pytest.ini pythonpath = ". server", regular packages always win
# over namespace portions, so a plain `import services...` would resolve
# to server/services. Load the aggregator service module directly from
# its file path instead (no production code touched).
_spec = importlib.util.spec_from_file_location(
    "china_policy_cleaning_service_under_test",
    AGGREGATOR_ROOT / "services" / "china_policy_cleaning_service.py",
)
china_policy_cleaning_service = importlib.util.module_from_spec(_spec)
sys.modules["china_policy_cleaning_service_under_test"] = china_policy_cleaning_service
_spec.loader.exec_module(china_policy_cleaning_service)

ChinaPolicyCleaningService = china_policy_cleaning_service.ChinaPolicyCleaningService  # noqa: E402


class StubDBService:
    """Minimal db_service double recording add_policy calls."""

    def __init__(self):
        self.added = []
        self.db_path = None

    def add_policy(self, policy):
        self.added.append(policy)
        return getattr(policy, "policy_id", "unknown_id")


# Synthetic MOCK policy text: {keyword} is the only industry trigger word.
MOCK_TEXT_TEMPLATE = """
《MOCK测试园区{label}产业扶持办法》
为促进{label}产业发展，园区管委会发布以下专项资金政策。
对相关企业给予研发补贴最高500万元。
"""


def _make_service(tmp_path):
    return ChinaPolicyCleaningService(StubDBService(), output_dir=str(tmp_path / "out"))


@pytest.fixture
def service(tmp_path):
    return _make_service(tmp_path)


# ============================================================
# 1. Production mapping values through the real runtime path
# ============================================================
class TestCleaningServiceProductionMapping:
    """Every value the production text extraction can emit must resolve
    correctly in the FINAL StructuredPolicy output (not just in
    basic_info)."""

    @pytest.mark.parametrize(
        "keyword,legacy,expected_canonical",
        [
            ("人工智能", "ai", "ai"),
            ("机器人", "robotics", "robotics"),
            ("量子计算", "quantum_computing", "quantum_computing"),
            ("半导体", "semiconductor", "semiconductor"),
            ("自动驾驶", "autonomous_driving", "autonomous_driving"),
            ("具身智能", "embodied_ai", "embodied_ai"),
            ("生物技术", "biotech", "biotech"),
            ("新能源", "new_energy", "new_energy"),
            ("新材料", "new_materials", "new_materials"),
            ("高端装备", "high_end_equipment", "high_end_equipment"),
        ],
    )
    def test_production_mapping_end_to_end(
        self, service, keyword, legacy, expected_canonical
    ):
        text = MOCK_TEXT_TEMPLATE.format(label=keyword)
        policy = service._clean_china_policy_text(
            text, "http://example.com/mock", "beijing_zhongguancun"
        )
        assert policy.industry == legacy
        assert policy.canonical_industry == expected_canonical


# ============================================================
# 2. Unknown safety: no silent guessing
# ============================================================
class TestCleaningServiceUnknownSafety:
    def test_no_industry_keyword_resolves_to_other_not_guess(self, service):
        text = "《MOCK测试园区一般性扶持通知》本通知不涉及任何特定行业。"
        policy = service._clean_china_policy_text(
            text, "http://example.com/mock", "shanghai_zhangjiang"
        )
        # "other" is an EXACT canonical id; it must surface as "other",
        # never as None and never as a guessed concrete industry.
        assert policy.industry == "other"
        assert policy.canonical_industry == "other"


# ============================================================
# 2. Backward compatibility: legacy field preserved, additive change
# ============================================================
class TestCleaningServiceBackwardCompatibility:
    def test_legacy_industry_value_untouched(self, service):
        text = MOCK_TEXT_TEMPLATE.format(label="人工智能")
        policy = service._clean_china_policy_text(
            text, "http://example.com/mock", "beijing_zhongguancun"
        )
        # legacy value survives untouched (not renamed/overwritten)
        assert policy.industry == "ai"

    def test_canonical_industry_is_additive(self, service):
        text = MOCK_TEXT_TEMPLATE.format(label="半导体")
        policy = service._clean_china_policy_text(
            text, "http://example.com/mock", "beijing_zhongguancun"
        )
        # adding canonical_industry must not alter any pre-existing field
        assert policy.country == "CN"
        assert policy.location == "beijing_zhongguancun"
        assert policy.policy_id.startswith("china_")
        assert isinstance(policy.incentives, list)
        assert isinstance(policy.requirements, list)
        assert isinstance(policy.compliance_standards, list)
        assert policy.metadata["data_quality"] == "estimated"
        assert policy.metadata["china_specific"]["currency"] == "CNY"

    def test_structured_policy_backward_compatible_construction(self):
        # Constructing StructuredPolicy without canonical_industry still
        # works (old callers unaffected).
        from processors.policy_cleaner import StructuredPolicy

        policy = StructuredPolicy(
            policy_id="p1",
            location="loc",
            country="CN",
            region="reg",
            industry="ai",
            policy_type="grant",
            title="t",
            description="d",
            incentives=[],
            requirements=[],
            compliance_standards=[],
            metadata={},
        )
        assert policy.canonical_industry is None


# ============================================================
# 3. Determinism: same input -> identical canonical output (20 runs)
# ============================================================
class TestCleaningServiceDeterminism:
    def test_canonical_output_deterministic_20_runs(self, service):
        text = MOCK_TEXT_TEMPLATE.format(label="人工智能")
        outputs = []
        for _ in range(20):
            policy = service._clean_china_policy_text(
                text, "http://example.com/mock", "beijing_zhongguancun"
            )
            outputs.append((policy.industry, policy.canonical_industry))
        assert len(set(outputs)) == 1
        assert outputs[0] == ("ai", "ai")

    def test_determinism_across_service_instances(self, tmp_path):
        text = MOCK_TEXT_TEMPLATE.format(label="量子计算")
        results = set()
        for i in range(5):
            svc = _make_service(tmp_path / f"run{i}")
            policy = svc._clean_china_policy_text(
                text, "http://example.com/mock", "hefei_hitech"
            )
            results.add((policy.industry, policy.canonical_industry))
        assert results == {("quantum_computing", "quantum_computing")}


# ============================================================
# 4. Batch entry point: full runtime chain incl. db hand-off
# ============================================================
class TestCleaningServiceBatchRuntime:
    def test_batch_chain_produces_canonical_industry(self, tmp_path, service):
        source = tmp_path / "beijing_zhongguancun_mock_policy.txt"
        source.write_text(
            MOCK_TEXT_TEMPLATE.format(label="人工智能"), encoding="utf-8"
        )
        report = service.batch_clean_china_policies([str(source)])
        assert report.successful_policies == 1
        assert report.failed_policies == 0
        assert len(service.db_service.added) == 1
        stored = service.db_service.added[0]
        assert stored.industry == "ai"
        assert stored.canonical_industry == "ai"

    def test_batch_mock_metadata_preserved(self, tmp_path, service):
        # filename must contain the Chinese region keyword so that
        # _detect_region_from_file maps it to shanghai_zhangjiang
        source = tmp_path / "张江mock政策文件.txt"
        source.write_text(
            MOCK_TEXT_TEMPLATE.format(label="半导体"), encoding="utf-8"
        )
        report = service.batch_clean_china_policies([str(source)])
        assert report.successful_policies == 1
        stored = service.db_service.added[0]
        # taxonomy integration must not alter quality/mock markers
        assert stored.metadata["data_quality"] == "estimated"
        assert stored.metadata["china_specific"]["region"] == "shanghai_zhangjiang"


# ============================================================
# 5. Exception handling: fail loudly, never emit wrong canonical value
# ============================================================
class TestCleaningServiceExceptionSafety:
    def test_registry_failure_propagates_from_text_cleaning(
        self, service, monkeypatch
    ):
        class BrokenRegistry:
            def resolve(self, value):
                raise RuntimeError("registry unavailable")

        monkeypatch.setattr(
            china_policy_cleaning_service, "_canonical_registry", BrokenRegistry()
        )
        text = MOCK_TEXT_TEMPLATE.format(label="人工智能")
        with pytest.raises(RuntimeError):
            service._clean_china_policy_text(
                text, "http://example.com/mock", "beijing_zhongguancun"
            )

    def test_registry_failure_marks_file_failed_no_bad_canonical(
        self, tmp_path, service, monkeypatch
    ):
        class BrokenRegistry:
            def resolve(self, value):
                raise RuntimeError("registry unavailable")

        monkeypatch.setattr(
            china_policy_cleaning_service, "_canonical_registry", BrokenRegistry()
        )
        source = tmp_path / "beijing_zhongguancun_mock_policy.txt"
        source.write_text(
            MOCK_TEXT_TEMPLATE.format(label="人工智能"), encoding="utf-8"
        )
        report = service.batch_clean_china_policies([str(source)])
        assert report.failed_policies == 1
        assert report.successful_policies == 0
        # nothing reached the db -> no policy carries a wrong canonical value
        assert len(service.db_service.added) == 0
