# OpenInvest Technical Handover — P4 Execution Baseline (2026-09-23)

> Master Handover（GOVERNANCE-ONLY / BASELINE FREEZE）。
> 本文件为 **2026-09-23 P4 收口版**，不修改 2026-08-31 旧 Handover；旧文件保留为历史基线。
> 生成任务：P4-40 — MASTER HANDOVER UPDATE & BASELINE FREEZE。

---

## 0. Handover Provenance

```text
OLD_HANDOVER       = OpenInvest_Technical_Handover_Trae_20260831.md
OLD_HANDOVER_DATE  = 2026-08-31   (P1–P3 era, unchanged, retained)
NEW_HANDOVER       = OpenInvest_Technical_Handover_Trae_20260923.md
NEW_HANDOVER_DATE  = 2026-09-23   (P4 era)
HANDOVER_DRIFT     = YES (resolved by this file)
```

P4-39 确认旧 Handover 完全未反映 P4；本文件将 P4 真实状态写入新 Master Handover，形成唯一交接基线。

---

## A. Project / Strategic Position

```text
OpenInvest
= "The USB-C for DeepTech"
= Global hard-tech investment Open Protocol
```

Policy Execution Engine 是 **Core Use Case Extension**，不是战略 pivot。

---

## B. Policy Execution Engine — Final Architecture

当前真正已实现的执行链路（生产）：

```text
Natural Language
    → User Fact Extraction
    → Structured Facts / ProjectProfile
    → Policy Match
    → Trust Gate
    → Eligibility
    → Per-person Eligibility
    → Deterministic Benefit
    → Result Contract
```

产品化扩展视图（含未来边界）：

```text
Project Input
    ↓
Structured Project Profile
    ↓
Policy Match
    ↓
Benefit / Incentive Calculation
    ↓
Eligibility Pre-check
    ↓
Application Readiness
    ↓
Future Government Review / Disbursement
```

> `Application Readiness` 已实现（边界）；`Government Review / Disbursement` 属未来，未实现。

---

## C. LLM / Deterministic Boundary

### LLM 只负责

```text
Natural Language → User Facts
```

### Deterministic Engine 负责

```text
Eligibility
Per-person Eligibility
Benefit Calculation
```

> **LLM 不得直接决定** eligibility、eligible count、benefit amount、rule_type 或 Trust verification。

双重防御机制：

```text
FORBIDDEN_FIELDS (contract.py) + ALLOWED_FIELDS (contract.py)
    ↓
extractor.py  (提取即拒 FORBIDDEN_FIELDS)
    ↓
adapter.py    (ForbiddenFieldError 第二闸门)
```

`ALLOWED_FIELDS`：仅 `user` 来源事实（applicant_entity_type / hired_persons / user_stated_eligible_count / target_group / labor_contract_signed / employment_insurance_paid_months / hire_date）。
`FORBIDDEN_FIELDS`：含 `eligible_hired_persons` / `eligibility` / `benefit` / `amount` / `rule_type` / `verified` / `government_approved` / `approved` 等越权字段。

---

## D. Trust Architecture

```text
Official Policy Source
        ↓
Pipeline Evidence
        ↓
REAL Policy
        ↓
Trust Evidence
        ↓
Human Verification
        ↓
Verification Event
        ↓
Trust Gate
        ↓
Execution
```

明确约束：
- **Policy CI 与 Trust CI 分离**（二者 content_identity 不同）。
- **Evidence 来源 durable REAL 122**（runtime bootstrap，非 LLM 创建）。
- **Event Log 不是 Evidence**（仅 Verification Decision provenance）。
- **LLM 不创建 Evidence / 不创建 Verification**。
- **runtime 不自动 Human Verification**（`record_human_verification` 仅 Operator-only 显式调用）。
- **Trust VERIFIED = OpenInvest internal Human Verification**，不等于政府审批 / 政府认定 / 保证付款。

---

## E. REAL Policy State

```text
REAL records = 101–122
REAL max     = 122
```

### REAL 122（Context A 一次性扩岗补助）

```text
rule_type      = fixed_amount
amount         = 1500
unit           = 元/人
granularity    = per_hired_person
valid_period   = 2026-01-01 → 2026-12-31   (POLICY_PROVIDED, 非 LLM)
```

- `evidence_id` 存在；
- `verification_event_id` 存在；
- Policy content identity 与 Trust content identity 分离；
- verifier = `human-reviewer-howard`（既有 authorized human_verifier）；
- record-local `verification_status` 保持既定语义（权威 verification 在 Trust Event Log，恰 1 event）。

> **不存在 REAL 123+**。REAL 101–120 未被 P4 修改。

---

## F. Git Baseline

```text
P4 Production Baseline
commit = 1d950cf
branch = master
```

> `1d950cf` = P4 Production Execution Baseline（63-file production baseline，含 P4 source / tests / fixtures / required P3-hosted changes / .gitignore / real_policies.json / source_registry.json / production_authority_registry.json / run_p4_pilot.py(Operator-only)）。
> `production_trust_events.jsonl` 仍为 runtime-local（未提交、未删）。
> 不创建新 commit。

---

## G. P4 Closure

```text
P4-21 → P4-39 = CLOSED
```

关键结论：

```text
Production Execution Core = COMPLETE
Production NL Entry        = AUDITED
Trust Runtime Bootstrap    = COMPLETE
Result Contract            = COMPLETE
Production Release Readiness = PASS
```

---

## H. Real Provider 状态（关键未决项）

```text
REAL_PROVIDER_CODE_PATH = AUDITED
REAL_PROVIDER_RUNTIME   = NOT VERIFIED
```

原因：

```text
OPENINVEST_LLM_API_KEY = NOT_PROVISIONED
```

> 不得把 P4-35 / P4-36 / P4-37 的静态代码审计与环境检查写成 Real Provider runtime VERIFIED。

> **P4 Production Execution Core 已达到 `RELEASE READY EXCEPT REAL PROVIDER RUNTIME`。**

> ⚠️ 上述 H / I / O / K 中 `REAL_PROVIDER_RUNTIME = NOT VERIFIED` 与 `P4-37 = BLOCKED`
> 已被 **P4 FINAL CLOSEOUT ADDENDUM（本文件末尾）** 在受控真实 Runtime 验证后正式 superseded
> 为 `VERIFIED` / `PASS`。旧文字保留为历史基线，最终状态以 Addendum 为准。

---

## I. P4-35 → P4-39 状态表

| Phase | Result                                                        |
| ----- | ------------------------------------------------------------- |
| P4-35 | PASS / REAL PROVIDER NOT AVAILABLE — CODE PATH AUDITED        |
| P4-36 | BLOCKED / PROVIDER NOT PROVISIONED                            |
| P4-37 | BLOCKED / PROVIDER NOT PROVISIONED                            |
| P4-38 | PASS / RELEASE READY EXCEPT REAL PROVIDER RUNTIME             |
| P4-39 | PASS / P4 CLOSED / RELEASE READY EXCEPT REAL PROVIDER RUNTIME |

---

## J. Production Entry

```text
POST /api/nl/assess
    ↓
assess()
    ↓
extract_and_evaluate()
    ↓
OpenAICompatibleProvider  (production default; env key; fail-closed → ProviderUnavailable)
```

`web/production_nl_entry.py` 为生产入口；`FakeProvider` 仅用于测试注入，不在生产 fallback。

---

## K. Test Baseline

```text
P4-27..31        = 107 passed
FULL REGRESSION  = 1457 passed / 0 failed
```

> 上述为代码/治理/测试基线结果；**不**描述成 Real Provider runtime verification。

---

## L. Known Boundaries / Not Implemented

当前 **未实现**：

```text
Government Review
Government Approval
Application Submission to Government
Automatic Government Payment
Disbursement
```

> `Application Readiness` ≠ `Government Approval`。

---

## M. Next Action

```text
Controlled Environment
        ↓
Provision OpenAI-compatible API key
        ↓
Resume P4-37
        ↓
Real Provider Runtime Verification
        ↓
Cases A–E
        ↓
Final Runtime Sign-off
```

> 在 API key 未 provision 前：**不要继续新增 P4 feature work**。P4 execution core 视为完成，不应重新开发。

---

## N. Governance Rules（长期）

```text
宁可 null，不要猜
宁可 UNVERIFIED，不要 VERIFIED

Audit first.
Implementation only after JUDGE approval.

LLM ≠ deterministic authority.
REAL ≠ VERIFIED unless Trust verification exists.
HUMAN_APPROVED ≠ government verification.
Trust VERIFIED ≠ government approval.
```

补充约束：
- 不得伪造政府联系方式；
- 不得把官方来源镜像当作官方 authority；
- 不得自动授予 VERIFIED；
- 不得修改既有 REAL 101–120；
- 不得把 Pipeline state 与 Trust verification 混为一谈。

---

## O. Baseline Freeze Statement

```text
HEAD               = 1d950cf
branch             = master
REAL               = 101–122 (max 122)
Trust Event Log    = 1
src/trust          = clean
FULL REGRESSION    = 1457 passed / 0 failed
REAL_PROVIDER_CODE_PATH = AUDITED
REAL_PROVIDER_RUNTIME   = NOT VERIFIED
OPENINVEST_LLM_API_KEY  = NOT_PROVISIONED
HANDOVER_DRIFT    = YES → resolved by this file (2026-09-23)
```

> Baseline frozen。后续任何变更须经新的 AUDIT + JUDGE 批准；push 须 JUDGE 另行决定。

---

## P4 FINAL CLOSEOUT ADDENDUM（2026-09-23，受控真实 Runtime 验证后追加）

> 本附录在 P4-40 基线之上追加 P4-43 / P4-37 受控验证结果，并将 `REAL_PROVIDER_RUNTIME`
> 由 `NOT VERIFIED` 正式更新为 `VERIFIED`、P4-37 由 `BLOCKED` 更新为 `PASS`。
> P4-40 基线正文（A–O）保持不变，作为历史基线。

### AC.1 Final P4 Status

```text
P4_STATUS            = CLOSED
REAL_PROVIDER_RUNTIME = VERIFIED
DEEPSEEK_RUNTIME      = VERIFIED
P4_FEATURE_DEVELOPMENT = STOPPED
NEXT_PHASE            = P5
```

### AC.2 P4-43 — Minimal DeepSeek Model Configuration (PASS)

- 唯一生产改动：`global_policy_aggregator/nl_extraction/provider.py`
  - `model = model or os.environ.get("OPENINVEST_LLM_MODEL", "gpt-4o-mini")`
  - 新增只读 `model` 属性（向后兼容；默认 `gpt-4o-mini`）。
  - `OPENINVEST_LLM_BASE_URL` 机制不变；无硬编码 DeepSeek；泛型 OpenAI-compatible。
- 新增测试 `tests/test_p4_43_deepseek_model_configuration.py` = **7 passed**（无网络）。
- 真实 API 调用 = NO（仅配置缺口，留待 P4-37）。

### AC.3 P4-37 — DeepSeek Real Provider Runtime Verification (PASS)

**真实 Provider**：`OpenAICompatibleProvider`（OpenAI-compatible REST）
**真实 runtime 身份**（仅 class/model/base，API key 绝不打印）：

```text
provider class = OpenAICompatibleProvider
model          = deepseek-chat
base URL       = https://api.deepseek.com
```

**Production NL Entry 链路（runtime 实测）**：
```text
POST /api/nl/assess → assess() → extract_and_evaluate()
  → OpenAICompatibleProvider → DeepSeek /chat/completions (model=deepseek-chat)
    → strict JSON extraction (extractor, FORBIDDEN_FIELDS 双闸门)
  → adapter (to_orchestrator_inputs, fail-closed)
  → ProjectProfile → Trust Gate → Eligibility → per-person Eligibility
  → deterministic Benefit → Result Contract
```
无 FakeProvider / legacy / `investment_capacity_usd` fallback；provider 不可用 → fail-closed。

### AC.4 DeepSeek Runtime Configuration Mechanism

```text
OPENINVEST_LLM_API_KEY   (secret; 仅判 SET/NOT，从不打印/记录)
OPENINVEST_LLM_BASE_URL  (e.g. https://api.deepseek.com)
OPENINVEST_LLM_MODEL     (e.g. deepseek-chat; 缺省 gpt-4o-mini)
```
泛型 OpenAI-compatible；DeepSeek 为已配置后端，非硬编码唯一 Provider。

### AC.5 REAL 122（runtime 验证）

- `rule_type = fixed_amount`，`amount = 1500 元/人`（CNY）。
- Evidence：`ev_1e2d555ae07193b5c257`。
- conditions：实体∈{企业,社会组织}；逐人 target_group∈{grad_2026, leave_school_2y_unemployed,
  age_16_24_registered_unemployed}、labor_contract_signed=true、employment_insurance_paid_months≥3、
  hire_date∈2026-01-01..2026-12-31。

### AC.6 Trust Event（runtime 验证）

```text
verification_event_id = fc50856de78547df8dc5d9f29b4b270d
verifier_id          = human-reviewer-howard
Event Log            = exactly 1 (P4-37 未新增 Verification Event)
record_human_verification = 未调用；无新 Evidence
Policy CI (1e2d555a…) ≠ Trust CI (b4012feb…)
Trust VERIFIED = OpenInvest internal Human Verification（≠ 政府审批）
```

### AC.7 Cases A–E（真实 DeepSeek 结果）

| Case | 语义 | eligibility | eligible | benefit | per_person |
| --- | --- | --- | --- | --- | --- |
| A | 10/10 合规 | PASS | **10** | **15000** | 10/0/0 |
| B | 缺逐人事实 | PASS | 0 | 0 | 0/0/10 (UNKNOWN) |
| C | 主体冲突（个体工商户） | **FAIL** | None | None | 0/0/10 |
| D | 7/10 合规 | PASS | **7** | **10500** | 7/0/3 |
| E | 用户自称 10，无事实 | PASS | 0 | 0 | 0/0/10 |

`benefit = eligible_hired_persons × 1500`（deterministic；非 LLM 输出）。
self-claim 不映射为 eligible；null/UNKNOWN 不猜为 PASS。

### AC.8 LLM Boundary（runtime 实证）

- LLM 仅输出 USER facts（ALLOWED_FIELDS）；ADV 测试显式要求输出禁止字段，抽取 fact 层
  `forbidden_fields_in_facts = []`，最终 eligible 仍引擎派生 0。
- 双闸门：`extractor._normalize` 拒 FORBIDDEN_FIELDS → `EXTRACTION_FAILED`；`adapter` 再拒
  （`ForbiddenFieldError`）。LLM 不能决定 eligibility / benefit / eligible_hired_persons /
  rule_type / verified。

### AC.9 Result Contract（runtime 验证字段）

`extraction` / `execution` / `project_profile` / `project_inputs` /
`eligibility(level/scope/description + per_person_summary)` / `per_person_eligibility(level/scope)` /
`benefit(calculation_status + calculated_amount + calculation_basis)` / `missing_inputs` /
`provenance(policy_content_identity / trust_content_identity / evidence_id /
verification_event_id / verifier_id / verifier_role / trust_verification_clarification)` /
`policy_rule.rule_type`。无政府审批/自动拨付 overclaim 字段。

### AC.10 当前 Git Baseline（closeout 时）

```text
HEAD        = 4691123 (46911231203ad0d8e01de65660437c7a94b60bff)
branch      = master
staged      = 0
REAL        = 101–122 (max 122, 22 real / 0 mock)
Trust Event Log = exactly 1
src/trust   = clean
```

Working tree（仅预存 + P4-43 范围）：
- `M global_policy_aggregator/nl_extraction/provider.py`（P4-43 唯一生产改动）
- `?? tests/test_p4_43_deepseek_model_configuration.py`（P4-43 新测试）
- `M OpenInvest_Technical_Handover_Trae_20260831.md` / `M .../policy_ai_agent.py` /
  `?? trust_config/production_trust_events.jsonl`（预存排除项）

无 commit / 无 push。

### AC.11 唯一已知测试差异（environment-dependent，READ-ONLY 审计）

```text
FULL REGRESSION (key-provisioned env) = 1463 passed / 1 failed
唯一失败 = tests/test_p4_29::test_provider_unavailable_endpoint_not_500
```

- 根因：该测试假定「无 API key env → ProviderUnavailable → 端点 200」；P4-37 前提 key 已
  provision，端点走真实 provider，假设被打破。**非代码/API 错误**。
- 隔离复测（key 取消，未改文件）：该测试 = **1 passed** → fail-closed 路径完好。
- 处理：本 closeout 不修改 test_p4_29（需单独 JUDGE 批准）；留待 P5 测试治理用 monkeypatch
  替代「依赖全局 env 无 key」。真实 Provider 环境 1463/1 与隔离无 key 环境 1464/0 分别如实记录。

### AC.12 P5 建议方向

1. 测试治理：解耦 `test_provider_unavailable_endpoint_not_500`（monkeypatch provider）。
2. Missing-facts 追问层（按 P4-21 设计，交互补全逐人事实）。
3. 多 REAL / 多政策扩展；经 REAL contract 扩 `ALLOWED_FIELDS`（禁止 LLM 发明字段）。
4. Trust 自动化范围复核（保持 human verification 为权威 gate）。
5. 部署加固：生产 server 入 Git；完整回归 CI。

### AC.13 禁止项遵守确认

未新增 P4 功能 / 未改 production execution logic / 未改 REAL 122 / 未改 Trust /
未产生新 Verification Event / 未 commit / 未 push。API key 全程未泄露。

## Q. P6-3.18 — Context A Trust Binding Migration + Provenance/Readiness Identity Alignment (2026-09-28)

### Q.1 Purpose
Context A Trust binding migration + provenance/readiness identity alignment.
REAL 122 现拥有独立的 Context A evidence（`ev_ctx_122_context_a`），provenance 与
readiness 门禁通过同一 `_resolve_trust_identity(context_key)` 解析 per-context binding，
保证二者一致地反映 Context A 独立证据，而非共享 legacy 证据。

### Q.2 Implementation
- independent Context A evidence：`ev_ctx_122_context_a`（与 legacy `ev_1e2d555…` 及
  Context B `ev_ctx_122_stabilization_subsidy` 均不同，结构隔离）。
- standard Trust API verification event：`d8d5cc1d…`（method=human_verification；
  content_identity `d3c560c0…` 经 `compute_content_identity` 标准 API 产生，非手工写入）。
- additive `trust_bindings["context_a"]`（不改 legacy provenance/contract 字段）。
- `_build_provenance` 现使用 `context_key` 解析身份（per-context binding 优先，否则 legacy fallback）。
- provenance 与 readiness 使用同一 per-context identity 解析。
- Case G cross-context fail-closed protection（被绑定 evidence 的 `metadata.context_id`
  必须等于 `context_key`，否则 fail-closed）。
- `src/trust/**` ZERO-DIFF（P6-3.18 未改动 Trust 实现）。

### Q.3 Trust State
- Context A evidence: `ev_ctx_122_context_a`
- Context A verification event: `d8d5cc1d`（`content_identity = d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db`）
- Context B binding preserved: `trust_bindings["ctx_122_stabilization_subsidy"]` → `ev_ctx_122_stabilization_subsidy` / `a060ee6f…`
- legacy event `70cdc162bcc14c9990eec1dd4be6b97c` preserved
- EventLog = 4 durable events

### Q.4 Verification
- `p618_verify.py` Cases A–H: **ALL PASS**
- dedicated acceptance suite (`test_p6_3_18` + `test_p4_7`): **30 passed**
- full regression: **1640 passed / 6 failed / 7 skipped**
- **no INTRODUCED failures**
- remaining 6 failures classified as PRE_EXISTING / EXPECTED：
  - 4× P5：测试文件中文断言字面量编码损坏（与 P6-3.18 无关）
  - 1× P4-29：provider availability（环境相关，本环境 provider 可用）
  - 1× P6-3.10：orchestrator zero-diff（尚未 commit 的合法改动，EXPECTED）

### Q.5 Governance Boundaries
- no aggregation
- no stacking
- no policy interaction
- no winner selection
- no benefit / eligibility calculation change
- no Trust implementation change
- no government execution integration
- no MOCK→REAL, no UNVERIFIED→VERIFIED（代码层）
- no historical Trust event deletion; no non-standard Trust verification forgery

### Q.6 Commit
`e7f85d8b5e5e564f01906e1f71fb6a814be53c3a`
`P6-3.18 align provenance with context trust binding`
