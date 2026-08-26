# Industry Taxonomy Consistency Audit

**Document**: `Industry_Taxonomy_Audit_20260826.md`  
**Quest**: P1-3.0 — Industry Taxonomy Consistency Audit  
**Type**: AUDIT ONLY — No Implementation  
**Date**: 2026-08-26  
**Status**: ✅ AUDIT COMPLETE · IMPLEMENTATION NOT STARTED  

---

## 1. Executive Summary

OpenInvest 项目中存在 **多套独立的行业分类体系（Industry Taxonomy）**，分布在不同组件中，彼此之间没有统一的规范或正式的映射关系。

本审计确认了 **至少 7 套独立的行业分类定义**，分布在 Parser、Schema、Web Portal、Seed Data、Cleaning Service 和 Legacy Crawler 中。

Handover Manual 中记录的 "5/8/21/12 categories" 已逐一追溯：

| 数字 | 来源 | 含义 | 验证状态 |
|---:|---|---|---|
| **5** | `schema/types.py` → `IndustryType` enum | 协议层行业类型枚举 | ✅ VERIFIED |
| **8** | `policy_cleaner.py` → `industry_mapping` 输出 | Parser 归一化后的 8 个不同英文值 | ✅ VERIFIED |
| **12** | `interactive_ai_server.py` → 12 条 Mock 政策 | Web Portal 中 12 个不同中文行业标签 | ✅ VERIFIED |
| **21** | 无法在当前代码库中找到确切来源 | 可能来自已删除的旧版本代码或文档 | ⚠️ UNVERIFIED |

**核心发现**：这些数字并非代表 4 套有明确定义的分类系统，而是 **不同组件各自独立定义的行业标签集合** 的大小。它们之间既无层级关系，也无正式映射。

---

## 2. Current Taxonomy Sources

### Taxonomy Source Inventory

| ID | Source | File | Location | Category Count | Purpose | Status |
|---|---|---|---|---:|---|---|
| T1 | Parser industry_mapping | `global_policy_aggregator/processors/policy_cleaner.py` L42-53 | 10 CN keys → 8 EN values | 8 | 文本归一化 | Active |
| T2 | Schema IndustryType | `schema/types.py` L25-31 | Enum 定义 | 5 | 协议类型约束 | Active |
| T3 | Web Portal policies | `global_policy_aggregator/web/interactive_ai_server.py` L24-457 | 12 条 Mock 政策 | 12 | UI 展示 | Active |
| T4 | Seed Data (original) | `global_policy_aggregator/data/seed_data/china_policy_seed_data.json` | 12 条政策 | 8 | 种子数据 | Active |
| T5 | Seed Data (detailed) | `global_policy_aggregator/data/seed_data/detailed_china_tech_policies.json` | 9 条政策 | 8 | 详细政策数据 | Active |
| T6 | Cleaning Service | `global_policy_aggregator/services/china_policy_cleaning_service.py` L277-288 | 10 CN keys → 10 EN values | 10 | 清洗服务归一化 | Active |
| T7 | Fixed/New Server industry_map | `global_policy_aggregator/web/fixed_server.py` L34-45 | 10 EN keys → 10 CN values | 10 | 英文→中文映射 | Active |
| T8 | Landing Service | `server/services/landing_requirements_service.py` L150-187 | 行业特定要求 | 3 | 落地要求 | Active |
| T9 | Legacy Mock DB | `policy_crawler/processors/mock_policy_database.py` L448-459 | 搜索映射 | 5 | 旧爬虫搜索 | Legacy |
| T10 | Evidence Graph (design) | `docs/Evidence_Graph_Prototype.md` L98 | TechnologyNode category | 6 | 设计文档 | Design Only |
| T11 | Legacy Mock DB targets | `policy_crawler/mock_policy_database.py` | target_industries | 5 | 旧目标行业 | Legacy |

---

## 3. 5 / 8 / 12 / 21 Analysis

### 3.1 — 5 Categories

**来源**: `schema/types.py` → `IndustryType` enum

```python
class IndustryType(str, Enum):
    AUTONOMOUS_DRIVING = "autonomous_driving"
    EMBODIED_AI = "embodied_ai"
    ROBOTICS = "robotics"
    AI_HARDWARE = "ai_hardware"
    QUANTUM_COMPUTING = "quantum_computing"
```

**含义**: 协议层（Server/Client API）使用的行业类型枚举。

**使用位置**:
- `schema/types.py` — 定义
- `server/services/landing_requirements_service.py` — 落地要求请求验证
- `server/services/tech_readiness_service.py` — 技术成熟度查询
- `docs/API.md` — API 文档（5 种类型列表）
- `tests/` — 测试中使用 `autonomous_driving` 和 `embodied_ai`

**关键发现**: 这 5 个值与 Parser/Seed Data 中的行业标签 **大部分不匹配**。例如：
- `ai_hardware` 在 Parser 和 Seed Data 中不存在
- `semiconductor`、`biotech`、`ai` 等 Seed Data 常用标签不在 enum 中
- 协议层实际上只实现了 3 个行业的落地要求（autonomous_driving, embodied_ai, quantum_computing）

### 3.2 — 8 Categories

**来源 A**: `policy_cleaner.py` → `industry_mapping` 输出值

```python
# 10 CN keys → 8 distinct EN values
"人工智能" → "ai"
"机器人" → "robotics"
"量子计算" → "quantum_computing"
"生物技术" → "biotech"
"自动驾驶" → "autonomous_driving"
"区块链" → "blockchain"
"虚拟现实" → "vr_ar"    # 两个 CN key 合并为 1 个 EN value
"增强现实" → "vr_ar"
"新材料" → "other"      # 两个 CN key 合并为 1 个 EN value
"新能源" → "other"
```

**Unique output values**: ai, robotics, quantum_computing, biotech, autonomous_driving, blockchain, vr_ar, other = **8**

**来源 B**: Seed Data JSON 文件中的 unique industry 值

- `china_policy_seed_data.json`: ai, quantum_computing, semiconductor, biotech, autonomous_driving, new_materials, blockchain, high_end_equipment = **8**
- `detailed_china_tech_policies.json`: ai, auto_driving, semiconductor, quantum_computing, biotechnology, new_energy, fintech, embodied_ai = **8**

**含义**: "8" 最可能指 Parser 归一化输出的 8 个不同值，巧合的是两个 Seed Data 文件也各自恰好有 8 个 unique industry。

### 3.3 — 12 Categories

**来源**: `interactive_ai_server.py` → 12 条 Mock 政策的 `industry` 字段

```
1. AI
2. 半导体
3. 自动驾驶
4. 量子计算
5. 区块链
6. 生物科技
7. 高端装备
8. 航空航天
9. 新材料
10. 新能源
11. 金融科技
12. 纳米技术
```

**含义**: Web Portal 展示层的 12 个中文行业标签。每条政策恰好使用不同的行业标签，因此 "12 条政策" = "12 个行业"。

**关键发现**: 这些是 **中文标签**，与 Parser 的英文输出值之间没有正式映射。例如：
- "AI" (Web) vs "ai" (Parser) — 大小写不一致
- "生物科技" (Web) vs "biotech" (Parser) — 需要翻译才能对应
- "纳米技术" (Web) — 在 Parser 中归入 "other"
- "金融科技" (Web) — 在 Parser 中不存在
- "航空航天" (Web) — 在 Parser 中不存在

### 3.4 — 21 Categories

**来源**: ⚠️ **UNVERIFIED — 无法在当前代码库中找到确切来源**

**可能解释**:
1. 可能来自早期版本的代码或文档，已在后续重构中删除
2. 可能是所有组件中所有 unique industry 标签的总数（但当前实际总数为 13-20+，取决于是否计算变体）
3. 可能是某个已删除的爬虫或数据源中的分类

**当前所有组件合并后的 unique industry 标签**（跨所有数据源）:

| 英文标签 | 出现来源 |
|---|---|
| ai | Parser, Seed Data, Cleaning Service |
| robotics | Parser, Schema |
| quantum_computing | Parser, Seed Data, Schema, Cleaning Service |
| biotech | Parser, Seed Data, Cleaning Service |
| autonomous_driving | Parser, Seed Data, Schema, Cleaning Service |
| blockchain | Parser, Seed Data |
| vr_ar | Parser |
| other | Parser |
| semiconductor | Seed Data, Cleaning Service, Fixed Server |
| new_materials | Seed Data, Cleaning Service |
| high_end_equipment | Seed Data, Cleaning Service |
| embodied_ai | Schema, Detailed Seed Data, Cleaning Service, Fixed Server |
| ai_hardware | Schema |
| auto_driving | Detailed Seed Data, Fixed Server |
| biotechnology | Detailed Seed Data, Fixed Server |
| new_energy | Cleaning Service, Detailed Seed Data, Fixed Server |
| fintech | Detailed Seed Data, Fixed Server, Web Portal |
| aerospace | Fixed Server |
| advanced_manufacturing | Fixed Server |
| nanotech (纳米技术) | Web Portal |

**总计**: 约 20 个 unique 标签（取决于是否将 `biotech`/`biotechnology` 和 `autonomous_driving`/`auto_driving` 视为相同）

**结论**: "21" 标记为 **UNVERIFIED**。当前代码库中无法确认其精确来源。

---

## 4. Parser Impact

### 4.1 Parser Taxonomy Dependency

**File**: `global_policy_aggregator/processors/policy_cleaner.py`

| 审计项 | 发现 |
|---|---|
| Parser 是否依赖 Industry Taxonomy？ | ✅ 是 — `industry_mapping` 用于文本→结构化数据的行业提取 |
| Parser 使用多少类别？ | 10 个中文输入 key → 8 个英文输出 value |
| Parser 的 category 输出？ | 字符串: ai, robotics, quantum_computing, biotech, autonomous_driving, blockchain, vr_ar, other |
| 是否存在 hard-coded categories？ | ✅ 是 — `industry_mapping` 字典硬编码在 `__init__` 中 |
| 是否存在 enum？ | ❌ 否 — 使用字符串匹配，无 enum 约束 |
| 是否存在 category mapping？ | ✅ 是 — CN→EN 映射 |
| 是否存在 unknown category？ | ✅ 是 — 未匹配的文本默认为 `"other"` |
| 是否存在 fallback？ | ✅ 是 — `basic_info.get("industry", "other")` |

### 4.2 Parser Impact Chain

```
Raw Policy Text (中文)
    ↓ keyword matching
industry_mapping (10 CN keys → 8 EN values)
    ↓ first-match wins
StructuredPolicy.industry (string, one of 8 values + "other")
    ↓ stored as-is
Seed Data / Database
    ↓ queried by industry
Web Portal / API
```

**关键风险**:
- First-match-wins 逻辑意味着文本中包含多个行业关键词时，只有第一个被匹配
- `"other"` 作为 fallback 会吞掉无法识别的行业（如 "纳米技术"、"金融科技"）
- Parser 的 8 个输出值与 Schema 的 5 个 enum 值 **大部分不兼容**

### 4.3 Cleaning Service 的独立 Parser

**File**: `global_policy_aggregator/services/china_policy_cleaning_service.py`

Cleaning Service 有自己独立的 `china_industry_mapping`（10 CN → 10 EN），与 Parser 的映射 **不同**:

| 差异 | Parser (policy_cleaner.py) | Cleaning Service |
|---|---|---|
| 半导体 | ❌ 不存在 | ✅ → semiconductor |
| 具身智能 | ❌ 不存在 | ✅ → embodied_ai |
| 新能源 | → other | ✅ → new_energy |
| 新材料 | → other | ✅ → new_materials |
| 高端装备 | ❌ 不存在 | ✅ → high_end_equipment |
| 虚拟现实/增强现实 | → vr_ar | ❌ 不存在 |

**结论**: 存在两个 **平行且不一致** 的 Parser 归一化逻辑。

### 4.4 Parser Impact Assessment

**Impact Level**: **HIGH**

修改 taxonomy 将影响:
1. `policy_cleaner.py` — 主 Parser 的 `industry_mapping`
2. `china_policy_cleaning_service.py` — 清洗服务的 `china_industry_mapping`
3. 所有依赖 Parser 输出的下游组件

---

## 5. Data Impact

### 5.1 Seed Data Taxonomy

**china_policy_seed_data.json** (12 policies):
- Industries: ai(2), quantum_computing(2), semiconductor(1), biotech(2), autonomous_driving(1), new_materials(1), blockchain(1), high_end_equipment(2)
- 使用 Parser 兼容的英文标签
- 8 unique industries

**detailed_china_tech_policies.json** (9 policies):
- Industries: embodied_ai(1), auto_driving(1), semiconductor(1), quantum_computing(1), ai(2), biotechnology(1), new_energy(1), fintech(1)
- 使用与 Parser **不兼容** 的标签（auto_driving vs autonomous_driving, biotechnology vs biotech）
- 8 unique industries

### 5.2 Web Portal Mock Data

**interactive_ai_server.py** (12 policies):
- 使用中文标签，与其他所有组件不兼容
- 12 unique industries（每个政策一个不同行业）

### 5.3 Data Issues

| 问题 | 描述 | 严重度 |
|---|---|---|
| 命名不一致 | biotech vs biotechnology | MEDIUM |
| 命名不一致 | autonomous_driving vs auto_driving | MEDIUM |
| 语言不一致 | 英文标签 vs 中文标签 | HIGH |
| 范围不一致 | 某些来源有 semiconductor，某些没有 | LOW |
| 无统一 ID | 没有行业分类的唯一标识符 | MEDIUM |

### 5.4 Data Impact Assessment

**Impact Level**: **HIGH**

修改 taxonomy 将影响:
- 2 个 Seed Data JSON 文件
- 1 个 Seed Data Generator
- Web Portal 的 12 条 Mock 政策
- Legacy Mock Policy Database

---

## 6. Test Impact

### 6.1 Taxonomy Test Dependency Map

| Test File | Industry Values Used | Hard-coded Count? | TEST COUPLING? |
|---|---|---|---|
| `tests/client/test_client.py` | autonomous_driving, embodied_ai | ❌ | No |
| `tests/server/test_server.py` | autonomous_driving, embodied_ai | ❌ | No |
| `tests/integration/test_integration.py` | autonomous_driving | ❌ | No |
| `tests/test_provenance.py` | (not industry-specific) | ❌ | No |
| `tests/test_trust_prototype.py` | (not industry-specific) | ❌ | No |
| `tests/test_trust_api_safety.py` | (not industry-specific) | ❌ | No |
| `tests/test_ui_mock_disclosure.py` | (checks mock labels, not industry count) | ❌ | No |

### 6.2 Test Coupling Analysis

**发现**: 当前测试 **没有** 硬编码行业分类数量（如 `assert len(categories) == X`）。

测试中使用的行业值主要来自 Schema `IndustryType` enum 的值（autonomous_driving, embodied_ai），这意味着：
- 测试与 Schema 耦合，但不与 Parser 或 Web Portal 的 taxonomy 耦合
- 修改 Schema enum 会影响测试
- 修改 Parser 或 Web Portal taxonomy 不会直接影响测试

### 6.3 Test Impact Assessment

**Impact Level**: **LOW**

当前测试对 taxonomy 变化的敏感度低。但如果未来增加 taxonomy 一致性测试，影响会上升。

---

## 7. Documentation Impact

### Documentation Taxonomy Matrix

| Document | Count | Meaning | Evidence | Consistent? |
|---|---:|---|---|---|
| `docs/API.md` | 5 | IndustryType enum 列表 | L285-291 列出 5 种类型 | ✅ 与 Schema 一致 |
| `README.md` | (uses examples) | 示例中使用 autonomous_driving, quantum_computing | L126, L142 | ✅ 与 Schema 一致 |
| `OpenInvest_Technical_Handover_Trae_20260826.md` | 5/8/21/12 | 记录为 Known Trap (TRAP-001) | L573, L1391 | ✅ 记录了不一致 |
| `docs/Evidence_Graph_Prototype.md` | 6 | TechnologyNode category | L98: 6 个枚举值 | ⚠️ 独立的第 3 套分类 |
| `docs/OpenInvest_Trust_Object_Model.md` | (field only) | industry_sector: string | L79 | ✅ 无具体数量声明 |
| `docs/Agent_Trust_Model.md` | (category field) | Agent category: string | L24 | ✅ 非行业分类 |
| `docs/Trust_Evidence_API.md` | (sector param) | find_company_evidence sector | L238-239 | ✅ 无具体数量声明 |
| `docs/DeepTech_Agent_Economy_Positioning.md` | (cross-sector) | 泛指跨领域合作 | L114 | ✅ 非行业分类 |
| `docs/Investor_Narrative_Guide.md` | (industry standard) | 泛指行业标准化 | L132 | ✅ 非行业分类 |

### 7.1 Documentation Consistency Finding

- API 文档与 Schema 一致（5 类）
- Handover Manual 正确记录了不一致问题
- Evidence Graph 设计文档有独立的 6 类 TechnologyNode category
- 其他文档未声明具体行业数量
- **没有文档声称 taxonomy 已统一**

---

## 8. Taxonomy Relationship Map

### 8.1 关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PARALLEL TAXONOMIES (无正式映射)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  T2: Schema IndustryType (5)                                        │
│  ┌──────────────────────────────────────────────┐                   │
│  │ autonomous_driving, embodied_ai, robotics,    │                   │
│  │ ai_hardware, quantum_computing                │                   │
│  └──────────────────────┬───────────────────────┘                   │
│                         │ 部分重叠（无正式映射）                       │
│  T1: Parser output (8)  │                                           │
│  ┌──────────────────┐   │                                           │
│  │ ai, robotics,    │   │                                           │
│  │ quantum_computing├───┘                                           │
│  │ biotech, auto_   │  ← autonomous_driving 重叠                    │
│  │ nomous_driving,  │  ← quantum_computing 重叠                     │
│  │ blockchain,      │  ← robotics 重叠                              │
│  │ vr_ar, other     │                                               │
│  └──────────────────┘                                               │
│         ↕ 无映射                                                     │
│  T6: Cleaning Service (10)                                          │
│  ┌──────────────────────────────────────────────┐                   │
│  │ ai, robotics, quantum_computing, semiconductor│                  │
│  │ autonomous_driving, embodied_ai, biotech,     │                   │
│  │ new_energy, new_materials, high_end_equipment │                   │
│  └──────────────────────┬───────────────────────┘                   │
│                         │ 部分重叠（无正式映射）                       │
│  T3: Web Portal CN (12) │                                           │
│  ┌──────────────────┐   │                                           │
│  │ AI, 半导体, 自动驾驶│   │                                         │
│  │ 量子计算, 区块链   │   │                                         │
│  │ 生物科技, 高端装备 │   │                                         │
│  │ 航空航天, 新材料   │   │                                         │
│  │ 新能源, 金融科技   │   │                                         │
│  │ 纳米技术          │   │                                         │
│  └──────────────────┘                                               │
│         ↕ 无映射                                                     │
│  T4/T5: Seed Data EN (8+8)                                          │
│  ┌──────────────────────────────────────────────┐                   │
│  │ ai, quantum_computing, semiconductor, biotech │                  │
│  │ autonomous_driving, new_materials, blockchain  │                  │
│  │ high_end_equipment, embodied_ai, auto_driving  │                  │
│  │ biotechnology, new_energy, fintech             │                  │
│  └──────────────────────────────────────────────┘                   │
│                                                                     │
│  T8: Landing Service (3)                                            │
│  ┌──────────────────────────────────────┐                           │
│  │ autonomous_driving, embodied_ai,     │                           │
│  │ quantum_computing                    │                           │
│  └──────────────────────────────────────┘                           │
│                                                                     │
│  T9: Legacy Mock DB (5)                                             │
│  ┌──────────────────────────────────────┐                           │
│  │ ai_ml, biotech, fintech, cleantech,  │                           │
│  │ blockchain                           │                           │
│  └──────────────────────────────────────┘                           │
│                                                                     │
│  T10: Evidence Graph Design (6)                                     │
│  ┌──────────────────────────────────────────────┐                   │
│  │ AI, BIOTECH, QUANTUM, CLEAN_TECH,            │                   │
│  │ ADVANCED_MATERIALS, OTHER                    │                   │
│  └──────────────────────────────────────────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 关系类型

**结论**: **PARALLEL TAXONOMIES — 无层级关系、无父子映射、无展示聚合**

各 taxonomy 之间仅有 **语义重叠**（如 "autonomous_driving" 出现在多个来源中），但 **没有代码级别的正式映射**。

已知的名称变体（同一行业的不同命名）:
- `biotech` ↔ `biotechnology` ↔ `生物科技`
- `autonomous_driving` ↔ `auto_driving` ↔ `自动驾驶`
- `ai` ↔ `AI` ↔ `人工智能`
- `quantum_computing` ↔ `量子计算`
- `semiconductor` ↔ `半导体`

---

## 9. Canonical Taxonomy Candidates

### 候选方案

| 方案 | 描述 | Evidence | Advantages | Risks |
|---|---|---|---|---|
| A. 以 Cleaning Service (10) 为基准 | 10 类覆盖最全面的 Parser 输出 | 10 个 CN→EN 映射，覆盖主流 DeepTech 行业 | 覆盖度最高，已有 CN→EN 映射 | 缺少 Web Portal 的某些类别（金融科技、纳米技术） |
| B. 以 Seed Data 合并集 (13) 为基准 | 合并两个 Seed Data 文件的 unique 值 | 13 个 unique EN 标签 | 基于实际数据 | 包含同义词（biotech/biotechnology）需清理 |
| C. 以 Schema IndustryType (5) 为基准 | 扩展现有 enum | 已有类型安全保障 | 类型安全，Pydantic 验证 | 覆盖度太低（5 类远不够） |
| D. 层级 taxonomy | 设计 parent→child 层级 | 无现有证据支持 | 最灵活，可统一所有来源 | 设计复杂度高，实现成本高 |
| E. 暂不统一 | 保持现状，记录差异 | 当前审计结果 | 零风险 | 不一致持续存在 |

### 9.1 Recommendation

**RECOMMENDATION**: **方案 D — 层级 taxonomy（分层设计）**

**理由**:
1. 不同组件有不同需求粒度（Schema 需严格 enum，Parser 需宽泛映射，UI 需友好标签）
2. 单一 flat taxonomy 无法同时满足所有需求
3. 层级设计可以保留现有组件的独立性，同时建立统一的上层规范

**建议层级结构**（初步，需进一步设计）:
```
Layer 1: Canonical Industry Registry (权威行业注册表)
    → 定义所有已知行业的唯一 ID 和标准名称
    → 约 15-20 个行业

Layer 2: Component-Specific Mappings
    → Schema enum → Layer 1 ID 映射
    → Parser output → Layer 1 ID 映射
    → Web Portal labels → Layer 1 ID 映射
    → Seed Data values → Layer 1 ID 映射

Layer 3: Display Names (per language/locale)
    → 中文显示名
    → 英文显示名
```

**注意**: 本 Quest 不实施此方案。仅作为下一阶段 Quest 的建议。

---

## 10. Migration Risk

### 10.1 影响范围

如果未来统一 taxonomy，以下组件需要修改:

| 组件 | 文件 | Impact |
|---|---|---|
| Parser | `policy_cleaner.py` | HIGH — 核心归一化逻辑 |
| Cleaning Service | `china_policy_cleaning_service.py` | HIGH — 独立归一化逻辑 |
| Schema | `schema/types.py` | MEDIUM — enum 扩展 |
| Seed Data | 2 JSON files + generator | MEDIUM — 行业标签迁移 |
| Web Portal | `interactive_ai_server.py` | MEDIUM — 中文标签映射 |
| Landing Service | `landing_requirements_service.py` | LOW — 仅 3 个行业 |
| Tests | 多个测试文件 | LOW — 无硬编码数量 |
| Documentation | API.md, Handover | LOW — 文档更新 |
| Trust Infrastructure | `src/trust/` | LOW — 不直接依赖行业分类 |
| Evidence Graph | `src/trust/evidence_graph.py` | LOW — sector 为自由字符串 |

### 10.2 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|---|---|---|---|
| 破坏现有测试 | LOW | HIGH | 渐进式迁移，先增加映射层 |
| Seed Data 不兼容 | MEDIUM | MEDIUM | 提供旧→新标签映射表 |
| Parser 输出变化 | HIGH | HIGH | 保持向后兼容的 fallback |
| Web Portal 显示中断 | MEDIUM | LOW | UI 标签可通过映射表更新 |

---

## 11. Open Questions

1. **"21" 的来源**: 需要确认 21 categories 是否来自已删除的代码/文档，还是来自外部需求
2. **行业分类的权威来源**: 是否应采用中国国家标准行业分类（GB/T 4754）作为基准？
3. **Industry 在 Trust Model 中的角色**: 行业分类是否应成为 Evidence Object 的一部分？当前 Trust Infrastructure 不直接依赖行业分类
4. **多语言支持**: 是否需要同时维护中英文行业标签的正式映射？
5. **层级 vs 扁平**: 最终 taxonomy 应是层级结构还是扁平列表？

---

## 12. NOT IMPLEMENTED

以下内容 **NOT IMPLEMENTED**:

- ❌ 统一行业分类
- ❌ 跨组件行业映射表
- ❌ 层级 taxonomy 设计
- ❌ Schema enum 扩展
- ❌ Parser taxonomy 迁移
- ❌ Seed Data taxonomy 迁移
- ❌ Web Portal taxonomy 迁移

本 Quest 仅完成审计。所有实施工作留待后续 Quest。

---

## 13. Next Decision Required

**下一阶段建议 Quest**: P1-3.1 — Industry Taxonomy Alignment Design

**目标**: 基于本审计结果，设计并实施统一行业分类方案

**前置决策**:
1. 确认 canonical taxonomy 的基准来源
2. 确认是否采用层级结构
3. 确认 "21" 的来源
4. 确认行业分类在 Trust Model 中的定位

---

*Audit Complete: 2026-08-26*  
*Implementation: NOT STARTED*  
*Quest: P1-3.0 STATUS: PASS*
