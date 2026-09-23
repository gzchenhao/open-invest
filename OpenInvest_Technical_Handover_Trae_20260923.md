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
