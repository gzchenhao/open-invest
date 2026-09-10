# Policy Ingestion Pipeline — Contract v1 (P3-0, JUDGE approved 2026-09)

Canonical record: `OpenInvest_Technical_Handover_Trae_20260831.md` (P3-0 section).
This file is the code-side summary for future agents.

## Purpose & boundary

The pipeline performs **DISCOVER → FETCH → PARSE → NORMALIZE → VALIDATE → INGEST**.
**The crawler is NOT a verification engine.** Every candidate is
`is_mock=false, verification_status="unverified"`. VERIFIED has no code path here.
Governance: 宁可 null，不要猜；宁可 UNVERIFIED，不要 VERIFIED.

Implemented / planned stages:
- **P3-1 (done)**: `source_registry.py` + `source_registry.json` (official allowlist),
  `fetcher.py` (fetch + raw snapshot + failure log).
- **P3-2 (done)**: `candidate.py` (Candidate + FieldEvidence) + `parser.py`
  (bs4/lxml → clean text + fail-safe ParseFailure) + `normalizer.py`
  (逐字段 null-safe 抽取 + canonical_taxonomy 映射 + 字段级 quote evidence)。
  复用的纯逻辑：canonical_taxonomy.get_registry().resolve()（industry）；
  金额/日期正则抽取为独立纯函数，仅在有明确证据时填充。contact 在 P3-2 暂不抽取。
- **P3-3 (validate, done)**: `validator.py`（P3-3 Validation v1 — Candidate 结构 / 证据链 /
  provenance / snapshot / 状态机合法性校验，输出 `ValidationResult` ∈
  {PASS, NEED_HUMAN_REVIEW, REJECTED}）+ `states.py`（PipelineState 枚举 + fail-closed 转移守卫）。
  `validate()` 只验证、不推进状态；仅 `promote_to_validated(candidate, result)` 在
  `result.status == PASS` 时允许 NORMALIZED→VALIDATED，绝不 STAGED / HUMAN_APPROVED / REAL，
  绝不写 `real_policies.json`，绝不产生 VERIFIED。
  content_hash 闭环：提供 `FetchResult` 时比对 `content_hash`，否则 NEED_HUMAN_REVIEW。
  **Snapshot 安全**：`resolve_snapshot_path()` 对 `snapshot_ref` 做 path-traversal 防护
  （拒绝绝对路径与 ".."，且最终路径必须位于 snapshots root 内，否则 raise）；
  `validate()` 在同时提供 `snapshot_bytes` 与磁盘 snapshot 且内容不一致时报
  "snapshot source conflict"（REJECTED，不静默选择其一）。
- **P3-4 (staging, done)**: `staging.py`（P3-4 Staging v1 — VALIDATED→STAGED→HUMAN_APPROVED
  受控推进 + 人审闸门 + append-only 落盘）。
  - `promote_to_staged(candidate, result, snapshots_dir=None)`：要求 `result.status == PASS` 且
    `result.observed_content_hash` 与当前 Candidate 快照内容身份一致（由
    `compute_candidate_content_identity()` 用 `resolve_snapshot_path` + `compute_content_hash`
    重算），否则 fail-closed（防旧 ValidationResult 重放）。仅改 `pipeline_state`/`pipeline_history`。
  - `human_approve(candidate, approval, snapshots_dir=None)`：要求 `STAGED` 态 + 显式 `HumanApproval`
    （verifier_id / verifier_role∈allowlist / approval_evidence / content_identity 匹配 /
    approved_at 合法 UTC / is_mock=false / verification_status="unverified"），任一不满足即拒绝；
    绝不接受空 approval / None / 字符串 / 默认值绕过。
  - **HUMAN_APPROVED ≠ VERIFIED**：`verification_status` 恒为 `"unverified"`，绝不调用
    `src/trust` 的 HumanVerificationGate，绝不产生 VERIFIED。
  - **禁止 REAL promotion**：无 `promote_to_real()`；状态机仅允许 `HUMAN_APPROVED → REJECTED`，
    绝不自动 `→ REAL`（id 121+ 留待后续人工流程）。
  - **Staging 持久化**：固定写 `data/raw_policies/staged/`（gitignored runtime artifact），
    append-only JSONL；无任意 output path 参数，绝不写 `real_policies.json`。
  - 复用 P3-1/P3-3 原语，不修改 P3-1/P3-2/P3-3 任何文件；无 LLM、无 crawler。
- **P3-6 (verification handoff, done)**: `trust_handoff.py`（P3-6 Verification Handoff —
  HUMAN_APPROVED → Trust EvidenceObject intake / registration）。
  - `create_verification_handoff(candidate, approval, snapshots_dir=None)`：要求 `HUMAN_APPROVED`
    态 + 显式 `HumanApproval`，**实时重算**当前 snapshot 内容身份（复用 P3-4
    `compute_candidate_content_identity`）并与 `approval.content_identity` 比对；
    snapshot 缺失 / 不可读 / hash 无法计算 / identity 缺失 / 不匹配 / Candidate 自带
    identity 冲突 → `InvalidTransitionError`（stale-approval fail-closed）。返回
    `VerificationHandoff`（handoff_status="created"）。
  - `register_evidence_object(handoff, trust_service)`：仅调用注入的
    `trust_service.create_evidence(evidence_data)` 将「待验证」Evidence 注册到 Trust；
    **绝不** import / 调用 `record_human_verification()`；`verification_status` 强制
    `"UNVERIFIED"`；metadata 透传跨层锚点 `policy_content_identity`（= snapshot sha256）+
    `snapshot_ref` + provenance + extracted_fields + human_approval。
  - **P3-6 = Verification Handoff / Trust Intake，不是 Verification**：不产生 VERIFIED、
    不写 `real_policies.json`、不做 REAL promotion（id 121+ 留待 P3-7）、不新增 REAL
    PipelineState、不自动 human verification / contact extraction / crawler / LLM。
  - Trust ownership 不变：Pipeline → Handoff → Trust intake → 真实 Human Verifier →
    Trust Human Verification Gate → VERIFIED（后两步属 P3-7 / Trust 层）。
  - 复用 P3-1/P3-3/P3-4 原语，不修改 states.py / staging.py / validator.py / candidate.py；
    不修改 `src/trust/**`；无 LLM、无 crawler。

## Key rules (do not violate)

1. **Registry allowlist**: only HTTP(S) URLs on `allowed_domains` of *enabled* sources
   may be fetched. Registry-external URLs are rejected. No automatic domain discovery;
   new sources are added by humans to the tracked `source_registry.json`.
2. **Snapshot** (`data/raw_policies/snapshots/`): runtime artifact, gitignored, never
   published; dedup by normalized-content SHA-256; source_url in policy records is
   permanent regardless of snapshot fate. Missing snapshot ⇒ no guessed fields.
   **Staging record** (`data/raw_policies/staged/`): runtime artifact, gitignored, append-only
   JSONL; records pipeline state + content identity + approval (if HUMAN_APPROVED). Never
   touches `real_policies.json`; no arbitrary output path.
3. **null-first**: `amount / requirements / eligibility / contact` have NO extraction
   code path in v1 (not "failed extraction" — deliberately absent). Every non-null
   extracted field must carry a verbatim quote from the snapshot
   (`extracted_fields_evidence`, enforced from P3-3 validate stage).
4. **Failure honesty**: failures are typed (timeout / connection_error / http_4xx /
   http_5xx / unexpected_content / url_not_allowed), logged to
   `fetch_failures.jsonl`, and never produce policies or fake successes.
5. **Existing 20 REAL policies**: never rewritten, never re-ingested, ids unchanged;
   they are the regression/contract fixture (grandfathered from the new provenance
   hard gate).
6. **Trust isolation**: no `src/trust/**` imports, no `verification_status` writes,
   no VERIFIED value, ever. Provenance for ingested policies lives in SIDECAR files
   (JUDGE decision), not in the portal policy schema.
