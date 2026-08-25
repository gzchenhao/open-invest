# Historical Data Exposure Audit（TASK-P0-2.2）

- **Audit Date**: 2026-08-24
- **Auditor**: AI Agent（Automated Historical Scan + Manual Classification）
- **最高原则**: 宁可发现风险，不要掩盖风险。本审计只记录、不清理、不重写历史。
- **Repository**: https://github.com/gzchenhao/open-invest.git
- **REMOTE_HEAD (origin/master)**: `8c38be15844d2e20b5893db6c7af3900922d2a02`
- **LOCAL HEAD**: `8c38be15844d2e20b5893db6c7af3900922d2a02`（三方一致，已含 TASK-P0-2 / P0-2.1 治理）

---

## 1. Audit Scope

对 `origin/master` 的**全部 11 个历史 commit** 执行只读静态扫描（`git grep` 遍历每个
commit 树），识别三类风险：

1. 虚构政府联系方式（电话 / 邮箱 / 联系人）
2. 虚构官方来源 URL（gov.cn 域名、AI 生成路径）
3. 虚构政策内容（补贴金额、申报条件、官方身份声称）

扫描模式：中国手机/固话号段正则、`gov.cn` URL、邮箱、"联系人/联系电话/官方联系方式"、
`MOCK|SYNTHETIC|is_mock|verification_status` 披露标记交叉比对。

**扫描不判定域名真实存在性**（未做 DNS 核验）；所有无法核验的域名一律视为"未验证"。

## 2. Commit Range

| Commit | 摘要 | 风险数据 | 披露标记数 |
|---|---|---|---|
| `a970ba5` | Initial commit | 无 | 0 |
| `5562695` | Clean up test files | 无 | 0 |
| `01ba935` | v3.1.0 Web Portal/PDF/Contact | **引入全部虚构数据** | 4 |
| `580ace3` | Handover constitution + taxonomy | 携带未治理数据 | 12 |
| `6c0e0e2` | docs: actual commit hash | 携带未治理数据 | 12 |
| `f449f57` | align repository reality | 携带未治理数据 | 12 |
| `1eaa39e` | TASK-P0-1 evidence | 携带未治理数据 | 12 |
| `ec2e196` | **P0-2 溯源治理** | seed/门户数据治理（标记+置 null） | 163 |
| `07a31cf` | P0-2 evidence | 同上 | 163 |
| `ca2926b` | **P0-2.1 展示层披露** | 9 个展示面强制 MOCK 横幅 | 230 |
| `8c38be1` | P0-2.1 evidence（当前 HEAD） | 同上 | 230 |

审计覆盖：`a970ba5..8c38be1` 全部 11 个 commit（AUDIT COMMITS = 11）。

## 3. Files Scanned

每个 commit 树全文扫描（`-I` 跳过二进制）；风险命中集中于 34 个文件（峰值 `01ba935`），
当前 HEAD（`8c38be1`）仍有 33 个文件含扫描模式命中（其中多数为已治理的 MOCK 标记、
测试断言或审计证据引用）。

## 4. Findings

### 4.1 HIST_CONTACT_FINDINGS（虚构政府联系方式）

| Commit | File | Line | Risk Type | Example | Current Status |
|---|---|---|---|---|---|
| 01ba935 起 | `global_policy_aggregator/agents/policy_ai_agent.py` | 792 | 虚构固话 | `"电话": "021-12345678"` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `policy_crawler/data/raw_policies/` 下 7 个 .txt | 各行 | 虚构固话/邮箱 | `咨询电话：021-12345678`、`Email: quantum@shanghai.gov.cn`、`0755-86543210` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `policy_crawler/data/raw_policies/shanghai_policies_sample.json` | 14 | 虚构固话 | `"phone": "021-12345678"` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `policy_crawler/data/structured_policies/shanghai-qingpu-ai-hub-2024.json` | 264 | 虚构固话 | `"phone": "021-12345678"` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `global_policy_aggregator/data/raw_policies/shanghai_ai_policy_2024.txt` | 68 | 虚构固话 | `咨询电话：021-12345678` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `global_policy_aggregator/test_frontend_data.html` | 40-41 | 虚构固话+邮箱 | `"phone": "010-82896688"`、`policy@zjpark.gov.cn` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `global_policy_aggregator/scripts/update_policy_data.py` | 17 | 虚构固话 | `"phone": "021-50800880"` | **仍在 HEAD，无 MOCK 标识** |
| 01ba935 起 | `global_policy_aggregator/scripts/populate_china_policies.py` | 39 | 虚构固话 | `"phone": "010-82896688"` | 仍在 HEAD，**已有 MOCK 声明头（P0-2）** |
| 01ba935 起 | `policy_crawler/data/raw_policies/sample_raw_policies.py` | 89 | 虚构固话 | `联系电话：021-12345678` | 仍在 HEAD，**已有 SYNTHETIC/MOCK 声明头（P0-2）** |
| 01ba935 起 | `policy_crawler/crawlers/china_crawler.py` | — | 虚构固话 | `010-12345678` | 仍在 HEAD（爬虫示例数据） |
| 01ba935–1eaa39e | `global_policy_aggregator/web/interactive_ai_server.py` | 33 | 虚构固话 | `"phone": "010-82896688"` | **已在 ec2e196 置 null + mock 标记** |
| 01ba935–1eaa39e | `global_policy_aggregator/data/seed_data/detailed_china_tech_policies.json` | 179 | 虚构固话 | `"phone": "010-12345678"` | **已在 ec2e196 置 null + mock 标记** |
| 01ba935 起 | 多个历史版本 | — | 虚构手机 | `138 0013 8000` 类占位号 | 历史存在；当前门户已清零 |

**已核验事实**：当前对外服务层（web templates、服务器渲染的首页/卡片/联系方式、PDF）
经 TASK-P0-2.1 治理 + TEST-UI-MOCK-001..006 保护，**不含上述任何虚构号码**；
虚构号码仅残留于仓库内静态数据文件（见 §5 HIGH 清单）。

### 4.2 HIST_SOURCE_URL_FINDINGS（虚构官方来源 URL）

| 类别 | 示例 | 出现位置 | Current Status |
|---|---|---|---|
| 疑似不存在域名（AI 生成） | `zjpark.gov.cn`、`shqp.gov.cn`、`zhangjiang.gov.cn`、`hfht.gov.cn`、`gzzh.gov.cn`、`hfep.gov.cn` | seed 数据（历史）、crawlers、test_frontend_data.html | seed 已治理；crawlers/test_frontend_data.html **仍在 HEAD** |
| 真实风格域名 + 虚构路径 | `shanghai.gov.cn/shanghai/node12345/20240101/u1ai12345.html`、`sz.gov.cn/ztzl/ai_policy`、`zgc.gov.cn/policy/ai_2024.html` | structured_policies、seed（历史） | structured_policies **仍在 HEAD**；seed 已治理 |
| 泛域名爬取配置 | `https://gov.cn`、`https://www.gov.cn` | `policy_crawler/crawlers/*.py` | 仍在 HEAD（爬虫 base_url，非政策声称） |

注：未执行 DNS/可达性核验。域名真实性一律 **UNVERIFIED**；路径为 AI 生成（`node12345`、
`u1ai12345`、`t20240115_123456` 等编号特征明显）。

### 4.3 虚构政策内容审计（分类）

**类别 1 — 明确 Mock（风险低）**：
`ec2e196` 之后的 seed 数据集（12+9 条，全部 `is_mock: true` / `verification_status: "mock"`）、
`mock_policy_database.py` 系列（MOCK 声明头）、`sample_raw_policies.py`（SYNTHETIC 声明头）、
测试夹具（`.invalid` 保留域）。

**类别 2 — 无 Mock 标识但形似真实政策（风险高）**：
- `01ba935..1eaa39e`（5 个历史 commit）：33 条政策 + 35 种虚构补贴金额表述
  （"最高补贴 500 万元"、"资助 2000 万元"等）以真实政策面貌呈现，无任何 MOCK 标识。
- **当前 HEAD 仍有 13 个静态文件**（§5 HIGH 清单）：虚构咨询电话写在形似政府公文的
  .txt 政策文本中，无披露标识。任何人下载这些文件即获得"看起来真实的假公文"。

**类别 3 — 明确声称 Official / Verified（最高风险）**：
- `01ba935..f449f57 前`：门户 UI 使用"官方联系方式"标题 + 虚构号码；README 曾含
  "verified government contact"、"500+"、"10,000+"、"sub-100ms"、"future A2A Ready" 等未经证实宣传。
- **当前状态**：门户"官方联系方式"字样已清零（TEST-UI-MOCK-004 保护），README 已在
  `f449f57` 降级，9 个展示面强制 MOCK 横幅（`ca2926b`）。**该类别在当前版本已消除，
  但历史 commit 中永久存在。**

## 5. Risk Classification

### HIGH（历史存在真实误导可能 / 当前树仍暴露）

**H1 — 历史误导（不可通过非重写手段消除）**：`01ba935`、`580ace3`、`6c0e0e2`、
`1eaa39e` 四个 commit 完整包含未标识的虚构政府联系方式、虚构来源 URL、虚构补贴金额与
"官方联系方式"UI。任何人均可 `git checkout` 这些版本。

**H2 — 当前树残留（13 个无标识文件，清单如下）**：

```
global_policy_aggregator/agents/policy_ai_agent.py
global_policy_aggregator/data/raw_policies/shanghai_ai_policy_2024.txt
global_policy_aggregator/scripts/update_policy_data.py
global_policy_aggregator/test_frontend_data.html
policy_crawler/crawlers/china_crawler.py
policy_crawler/data/raw_policies/sample_shanghai_policy.txt
policy_crawler/data/raw_policies/shanghai_ai_policy.txt
policy_crawler/data/raw_policies/shanghai_policies_sample.json
policy_crawler/data/raw_policies/shanghai_pudong_ai_policy.txt
policy_crawler/data/raw_policies/shanghai_quantum_policy.txt
policy_crawler/data/raw_policies/shanghai_zhangjiang_tax_policy.txt
policy_crawler/data/raw_policies/shenzhen_autonomous_driving_requirements.txt
policy_crawler/data/structured_policies/shanghai-qingpu-ai-hub-2024.json
```

（另有 2 个文件含虚构号码但已有 MOCK 声明头：`populate_china_policies.py`、
`sample_raw_policies.py` —— 归入 MEDIUM。`policy_crawler/data/structured_policies/`
另两个 JSON 含虚构来源 URL 但无号码 —— 同样归入 HIGH 观察项。）

### MEDIUM（历史存在但当前版本已隔离/已标记）

- seed 数据集（`china_policy_seed_data.json/.sql`、`detailed_china_tech_policies.json`）：
  历史版本含虚构数据，当前版本已 `is_mock` 标记 + 联系方式置 null（ec2e196）。
- 门户内嵌政策与全部对外展示面：已强制披露（ca2926b）。
- 含 MOCK 声明头但仍保留虚构号码的 2 个脚本/样本文件。
- 爬虫文件中的 `gov.cn` base_url（未验证域名，属爬取配置非政策声称）。

### LOW（已有 Mock 标识 / 刻意保留的治理证据）

- 测试夹具中的虚构号码（`tests/test_provenance.py`、`tests/test_ui_mock_disclosure.py`）：
  用作**负向断言**（验证治理系统拒绝/屏蔽这些数据），属防线而非风险。
- Handover / 本审计文档引用虚构号码作为证据记录。
- 全部 `is_mock: true` 的当前数据集。

## 6. Recommended Action

1. **（不执行，仅建议）** 对 H2 清单 13 个文件执行"标识或隔离"：追加
   SYNTHETIC/MOCK 声明头，或移入带 `README_QUARANTINE.md` 的隔离目录。
   —— 属内容修改，**需要人工批准**。
2. **（不执行，仅建议）** 若法律风险评估认为 H1 不可接受，唯一手段是历史重写
   （filter-repo/BFG + force push + 所有克隆失效）。**本审计明确未执行，需单独明确授权。**
3. **（建议立即考虑）** 在 H1/H2 处置完成前，评估将仓库临时设为 private。
   —— 属仓库设置变更，**需要人工批准**。
4. **（已自动完成）** TEST-HISTORY-001..003 将 H2 清单固化为受测试监管的
   "隔离清单"：清单内文件为已知风险；任何**新增**虚构联系方式文件将直接导致测试失败。
5. **（已自动完成）** 未来真实政策准入规范见 `docs/Policy_Data_Governance.md`。

### 需要人工批准：YES

任何超出"只读审计 + 测试 + 文档记录"的补救动作（数据文件修改、隔离移动、历史重写、
仓库可见性变更）均需仓库所有者明确书面授权。本次审计未改动任何被审计数据。

---

*审计证据：扫描输出为一次性脚本产物（未入库）；结论可由
`git grep -n -E "021-12345678|010-82896688|quantum@shanghai" <commit>` 在任意
commit 上独立复现。*
