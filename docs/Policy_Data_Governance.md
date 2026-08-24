# Policy Data Governance（真实政策数据准入规范）

- **生效日期**: 2026-08-24（TASK-P0-2.2）
- **上位约束**: `Qoder_Technical_Handover_20260824.md` §3 INV-007（DATA-INTEGRITY-001..005）
- **最高纪律**: 宁可 null，不要猜。宁可 UNVERIFIED，不要 VERIFIED。宁可少一条政策，不要多一条假的政策。

---

## 1. 状态定义（唯一合法枚举）

| 状态 | 定义 | 允许展示方式 |
|---|---|---|
| `MOCK` | 演示/合成数据，无真实来源 | 必须全局横幅 + 卡片级标签 + 文档免责声明 |
| `UNVERIFIED` | 来源未知或无法核验 | 必须标注"未核验"，禁止展示为官方信息 |
| `PARTIALLY_VERIFIED` | 官方来源存在，但部分字段（日期/金额/联系方式）无法确认 | 未确认字段必须为 null，逐字段标注 |
| `VERIFIED` | 官方来源已找到并逐项核验 | 允许展示，但必须随附完整溯源元数据（§2） |

技术约束：`url_status`（URL 可达性）≠ `source_verification_status`（来源真实性）。
HTTP 200 永远不能作为 `VERIFIED` 的证据。

## 2. VERIFIED 准入要求（缺一不可）

任何数据进入 `VERIFIED` 状态前，**必须**具备以下全部字段（缺一即降级为
`UNVERIFIED` 或拒绝入库）：

| 字段 | 要求 |
|---|---|
| `source_url` | 官方原始页面，真实可访问，且非占位符/AI 生成路径 |
| `source_title` | 官方页面上的原始标题（逐字抄录，禁止改写） |
| `publisher` | 发布机构官方全称 |
| `published_date` | 官方页面标注的发布日期；无法确认必须为 null，禁止推断 |
| `effective_date` | 官方文本标注的生效日期；无法确认必须为 null |
| `retrieved_at` | 本系统抓取时刻（ISO 8601） |
| `snapshot` | 抓取时的原文快照（存档哈希或归档文件），防止来源页事后变更无法对证 |
| `confidence` | 核验置信度说明（谁核验、核验了什么、哪些字段未能核验） |
| `verification_method` | `official_portal_manual` / `official_portal_agent` / `gazette_crosscheck` 等，禁止填 `inferred` |

## 3. 硬性禁止规则

1. **没有官方来源：禁止 `VERIFIED`。**
2. **没有人工或 Agent 实际执行验证并留痕：禁止显示 "Official" / "官方" / "Verified"。**
3. 禁止虚构任何政府部门联系方式；未知联系方式必须为 `null`（DATA-INTEGRITY-003）。
4. 禁止使用真实政府域名拼接虚构路径（如 `xx.gov.cn/node12345/...`）。
5. 测试夹具中的虚构数据必须使用 IANA 保留域（`.invalid`）或 `example.com`，
   禁止在测试中伪造真实政府域名。
6. Mock 数据必须显式标记（`is_mock: true` + `verification_status: "mock"`），
   且任何展示面必须带免责声明（DATA-INTEGRITY-005）。
7. 治理动作只允许"标记 + 置 null"，禁止静默删除记录（INV-000）。
8. Git 历史重写（filter-repo / filter-branch / BFG / force push）未经仓库所有者
   明确书面授权一律禁止。

## 4. 核验工作流（VERIFIED 唯一合法路径）

```
发现候选政策
  → 定位官方原始页面（政府门户/公报，不接受新闻转述作为唯一来源）
  → 逐字段比对：标题 / 发布机构 / 发布日期 / 金额 / 条件
  → 留存 snapshot（原文快照 + 抓取时间）
  → 填写 §2 全部 9 个字段
  → provenance_validator.validate_policy_record() 通过
  → 人工复核签字（记录核验人）
  → 方可置 verification_status = "verified"
```

任何一步失败 → 状态停留在 `UNVERIFIED` / `PARTIALLY_VERIFIED`，对外展示必须带相应标注。

## 5. 防回归测试绑定

| 测试 | 守护内容 |
|---|---|
| TEST-PROVENANCE-001..006 | Mock 不得冒充 Verified；Verified 必须有 source_url；联系方式溯源 |
| TEST-UI-MOCK-001..006 | 全部对外展示面强制 MOCK 披露 |
| TEST-HISTORY-001 | 当前代码不得新增虚构政府联系方式（隔离清单之外的文件零容忍） |
| TEST-HISTORY-002 | VERIFIED 政策必须有 source_url；当前数据集 0 条 VERIFIED |
| TEST-HISTORY-003 | MOCK 政策必须显示 disclaimer |

## 6. 已知历史风险

见 `docs/Historical_Data_Exposure_Audit_20260824.md`：
本规范生效前的历史数据存在未标识的虚构内容（HIGH 风险），已记录、未清理；
任何补救需人工批准。
