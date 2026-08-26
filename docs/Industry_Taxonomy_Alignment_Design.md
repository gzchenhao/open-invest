# Industry Taxonomy Alignment Design

**Document**: `Industry_Taxonomy_Alignment_Design.md`  
**Quest**: P1-3.1 — Canonical Industry Taxonomy Design  
**Type**: DESIGN ONLY — No Destructive Migration  
**Date**: 2026-08-26  
**Depends on**: P1-3.0 Industry Taxonomy Audit (`Industry_Taxonomy_Audit_20260826.md`)  
**Status**: ✅ DESIGN COMPLETE · IMPLEMENTATION NOT STARTED  

---

## 1. Problem Statement

OpenInvest 项目中存在 **11 套独立的行业分类定义**（P1-3.0 审计确认），分布在 Parser、Schema、Web Portal、Seed Data、Cleaning Service、Landing Service 和 Legacy Crawler 中。

这些分类之间：
- 无统一规范
- 无正式映射
- 命名不一致（biotech/biotechnology, autonomous_driving/auto_driving）
- 语言不一致（英文标签 vs 中文标签）
- 范围不一致（某些来源有半导体，某些没有）

**目标**：建立一个可验证、可迁移、可回滚的 Canonical Industry Taxonomy，使所有组件能够通过映射表指向同一套权威行业注册表。

---

## 2. Current Parallel Taxonomies

| ID | Source | File | Count | Type | Status |
|---|---|---|---:|---|---|
| T1 | Parser | `policy_cleaner.py` | 8 | CN→EN mapping | Active |
| T2 | Schema | `schema/types.py` | 5 | Enum | Active |
| T3 | Web Portal | `interactive_ai_server.py` | 12 | CN labels | Active |
| T4 | Seed Data (original) | `china_policy_seed_data.json` | 8 | EN values | Active |
| T5 | Seed Data (detailed) | `detailed_china_tech_policies.json` | 8 | EN values | Active |
| T6 | Cleaning Service | `china_policy_cleaning_service.py` | 10 | CN→EN mapping | Active |
| T7 | Fixed Server | `fixed_server.py` | 10 | EN→CN mapping | Active |
| T8 | Landing Service | `landing_requirements_service.py` | 3 | EN values | Active |
| T9 | Legacy Mock DB | `policy_crawler/processors/mock_policy_database.py` | 5 | EN values | Legacy |
| T10 | Deeptech Schema | `schemas/deeptech_policy_schema.json` | 21 | JSON Schema enum | **Unused** |
| T11 | Evidence Graph | `docs/Evidence_Graph_Prototype.md` | 6 | Design doc | Design Only |

---

## 3. Taxonomy Source Matrix

### 3.1 All Known Industry Values Across All Sources

| Canonical ID | T1 | T2 | T3(CN) | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ai | ✅ | | AI | ✅ | ✅ | ✅ | ✅ | | ai_ml | | AI |
| robotics | ✅ | ✅ | | | | ✅ | | | | ✅ | |
| quantum_computing | ✅ | ✅ | 量子计算 | ✅ | ✅ | ✅ | ✅ | ✅ | | ✅ | QUANTUM |
| biotech | ✅ | | 生物科技 | ✅ | | ✅ | | | | ✅ | BIOTECH |
| autonomous_driving | ✅ | ✅ | 自动驾驶 | ✅ | | ✅ | | ✅ | | ✅ | |
| blockchain | ✅ | | 区块链 | ✅ | | | | | ✅ | ✅ | |
| vr_ar | ✅ | | | | | | | | | ✅ | |
| semiconductor | | | 半导体 | ✅ | ✅ | ✅ | ✅ | | | ✅ | |
| new_materials | | | 新材料 | ✅ | | ✅ | | | | | ADVANCED_MATERIALS |
| high_end_equipment | | | 高端装备 | ✅ | | ✅ | | | | | |
| embodied_ai | | ✅ | | | ✅ | ✅ | ✅ | ✅ | | ✅ | |
| ai_hardware | | ✅ | | | | | | | | | |
| new_energy | | | 新能源 | | | ✅ | ✅ | | | cleantech | CLEAN_TECH |
| fintech | | | 金融科技 | | | | ✅ | | | ✅ | |
| aerospace | | | 航空航天 | | | | ✅ | | | ✅ | |
| nanotech | | | 纳米技术 | | | | | | | ✅ | |
| space_tech | | | | | | | | | | ✅ | |
| cybersecurity | | | | | | | | | | ✅ | |
| iot | | | | | | | | | | ✅ | |
| 5g | | | | | | | | | | ✅ | |
| edge_computing | | | | | | | | | | ✅ | |
| metaverse | | | | | | | | | | ✅ | |
| web3 | | | | | | | | | | ✅ | |
| digital_twin | | | | | | | | | | ✅ | |
| auto_driving | | | | | ✅ | | ✅ | | | | |
| biotechnology | | | | | ✅ | | ✅ | | | | |
| advanced_manufacturing | | | | | | | ✅ | | | |
| other | ✅ | | | | | | | | | | OTHER |
| unknown | | | | | | | | | | | |

**Synonym pairs** (same industry, different names):
- `biotech` ↔ `biotechnology` ↔ `生物科技`
- `autonomous_driving` ↔ `auto_driving` ↔ `自动驾驶`
- `ai` ↔ `ai_ml` ↔ `AI` ↔ `人工智能`
- `new_energy` ↔ `cleantech` ↔ `新能源` (partial overlap)

---

## 4. Canonical Taxonomy Principles

**PRINCIPLE-001**: Machine-readable stable IDs  
所有 canonical ID 使用小写英文 + 下划线格式（snake_case）

**PRINCIPLE-002**: One concept = one ID  
同义词必须归一化到单一 canonical ID

**PRINCIPLE-003**: 宁可 UNKNOWN，不要错误映射  
无法可靠映射的 legacy value → `unknown`

**PRINCIPLE-004**: 与 Trust Infrastructure 解耦  
Taxonomy 不影响 Trust Score、Provenance、Evidence Object

**PRINCIPLE-005**: 向后兼容  
现有数据必须继续可读，不强制迁移

**PRINCIPLE-006**: 中文显示名独立维护  
Display names 通过映射表获取，不硬编码在 canonical ID 中

**PRINCIPLE-007**: 可扩展  
新增行业不需要修改现有 ID，只需在 Registry 中添加新条目

**PRINCIPLE-008**: 不追加大流行词  
T10 中的 metaverse、web3、digital_twin、5g、edge_computing、iot 等需要评估是否属于 OpenInvest 核心范围

---

## 5. Proposed Canonical Registry

### 5.1 Design Rationale

T10 (deeptech_schema 21类) 包含大量过于细粒度的类别（5g, edge_computing, metaverse, web3, digital_twin），这些更适合归入更广泛的类别。

T2 (Schema 5类) 覆盖度不足，缺少 semiconductor、biotech、ai 等核心行业。

**本设计选择 16 个 canonical categories**，基于以下依据：
- 覆盖所有 Active 来源中实际使用的行业
- 合并同义词
- 将过于细粒度的类别归入更广泛的父类
- 保留 OpenInvest DeepTech 定位的核心行业

### 5.2 Canonical Industry Registry (Layer 1)

| # | Canonical ID | 中文名称 | English Display Name | Design Basis |
|---:|---|---|---|---|
| 1 | `ai` | 人工智能 | Artificial Intelligence | 核心 DeepTech 行业；合并 ai_ml |
| 2 | `robotics` | 机器人 | Robotics | 核心 DeepTech 行业 |
| 3 | `embodied_ai` | 具身智能 | Embodied AI | 新兴交叉领域（AI + Robotics） |
| 4 | `quantum_computing` | 量子计算 | Quantum Computing | 核心 DeepTech 行业 |
| 5 | `semiconductor` | 半导体 | Semiconductor | 核心 DeepTech 行业 |
| 6 | `biotech` | 生物医药 | Biotechnology | 核心 DeepTech 行业；合并 biotechnology |
| 7 | `autonomous_driving` | 自动驾驶 | Autonomous Driving | 核心 DeepTech 行业；合并 auto_driving |
| 8 | `aerospace` | 航空航天 | Aerospace & Defense | 核心 DeepTech 行业；合并 space_tech |
| 9 | `new_energy` | 新能源 | New Energy & CleanTech | 核心 DeepTech 行业；合并 cleantech |
| 10 | `new_materials` | 新材料 | Advanced Materials | 核心 DeepTech 行业；合并 nanotech |
| 11 | `blockchain` | 区块链 | Blockchain & Web3 | 合并 web3 |
| 12 | `fintech` | 金融科技 | FinTech | 保留 |
| 13 | `high_end_equipment` | 高端装备 | Advanced Manufacturing | 合并 advanced_manufacturing |
| 14 | `cybersecurity` | 网络安全 | Cybersecurity | 从 T10 提升 |
| 15 | `iot` | 物联网 | Internet of Things | 从 T10 提升；合并 5g, edge_computing |
| 16 | `vr_ar` | 虚拟现实/增强现实 | VR/AR & Metaverse | 合并 metaverse, digital_twin |
| — | `other` | 其他 | Other / Unknown | 兜底类别 |
| — | `unknown` | 未知 | Unknown | 无法识别的行业 |

**总计**: 16 canonical categories + other + unknown = **18 slots**

### 5.3 Canonical ID 设计规则

- 格式: `snake_case` 小写英文
- 稳定性: 一旦分配，永不重用
- 唯一性: 每个概念对应一个 ID
- 可读性: ID 本身具有语义

---

## 6. Canonical Industry IDs

```python
CANONICAL_INDUSTRY_REGISTRY = {
    "ai":                   {"zh": "人工智能",         "en": "Artificial Intelligence"},
    "robotics":             {"zh": "机器人",           "en": "Robotics"},
    "embodied_ai":          {"zh": "具身智能",         "en": "Embodied AI"},
    "quantum_computing":    {"zh": "量子计算",         "en": "Quantum Computing"},
    "semiconductor":        {"zh": "半导体",           "en": "Semiconductor"},
    "biotech":              {"zh": "生物医药",         "en": "Biotechnology"},
    "autonomous_driving":   {"zh": "自动驾驶",         "en": "Autonomous Driving"},
    "aerospace":            {"zh": "航空航天",         "en": "Aerospace & Defense"},
    "new_energy":           {"zh": "新能源",           "en": "New Energy & CleanTech"},
    "new_materials":        {"zh": "新材料",           "en": "Advanced Materials"},
    "blockchain":           {"zh": "区块链",           "en": "Blockchain & Web3"},
    "fintech":              {"zh": "金融科技",         "en": "FinTech"},
    "high_end_equipment":   {"zh": "高端装备",         "en": "Advanced Manufacturing"},
    "cybersecurity":        {"zh": "网络安全",         "en": "Cybersecurity"},
    "iot":                  {"zh": "物联网",           "en": "Internet of Things"},
    "vr_ar":                {"zh": "虚拟现实/增强现实", "en": "VR/AR & Metaverse"},
    "other":                {"zh": "其他",             "en": "Other"},
    "unknown":              {"zh": "未知",             "en": "Unknown"},
}
```

---

## 7. Chinese Display Names

| Canonical ID | 中文名称 |
|---|---|
| ai | 人工智能 |
| robotics | 机器人 |
| embodied_ai | 具身智能 |
| quantum_computing | 量子计算 |
| semiconductor | 半导体 |
| biotech | 生物医药 |
| autonomous_driving | 自动驾驶 |
| aerospace | 航空航天 |
| new_energy | 新能源 |
| new_materials | 新材料 |
| blockchain | 区块链 |
| fintech | 金融科技 |
| high_end_equipment | 高端装备 |
| cybersecurity | 网络安全 |
| iot | 物联网 |
| vr_ar | 虚拟现实/增强现实 |
| other | 其他 |
| unknown | 未知 |

---

## 8. English Display Names

| Canonical ID | English Display Name |
|---|---|
| ai | Artificial Intelligence |
| robotics | Robotics |
| embodied_ai | Embodied AI |
| quantum_computing | Quantum Computing |
| semiconductor | Semiconductor |
| biotech | Biotechnology |
| autonomous_driving | Autonomous Driving |
| aerospace | Aerospace & Defense |
| new_energy | New Energy & CleanTech |
| new_materials | Advanced Materials |
| blockchain | Blockchain & Web3 |
| fintech | FinTech |
| high_end_equipment | Advanced Manufacturing |
| cybersecurity | Cybersecurity |
| iot | Internet of Things |
| vr_ar | VR/AR & Metaverse |
| other | Other |
| unknown | Unknown |

---

## 9. Legacy → Canonical Mapping Matrix (Layer 2)

### 9.1 T1: Parser (policy_cleaner.py) → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| ai | ai | EXACT |
| robotics | robotics | EXACT |
| quantum_computing | quantum_computing | EXACT |
| biotech | biotech | EXACT |
| autonomous_driving | autonomous_driving | EXACT |
| blockchain | blockchain | EXACT |
| vr_ar | vr_ar | EXACT |
| other | other | EXACT |

### 9.2 T2: Schema IndustryType → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| autonomous_driving | autonomous_driving | EXACT |
| embodied_ai | embodied_ai | EXACT |
| robotics | robotics | EXACT |
| ai_hardware | **unknown** | ⚠️ NO DIRECT MATCH — ai_hardware 可考虑归入 ai 或 semiconductor，但无可靠依据 |
| quantum_computing | quantum_computing | EXACT |

### 9.3 T3: Web Portal CN Labels → Canonical

| Legacy Value (CN) | Canonical ID | Confidence |
|---|---|---|
| AI | ai | EXACT |
| 半导体 | semiconductor | EXACT |
| 自动驾驶 | autonomous_driving | EXACT |
| 量子计算 | quantum_computing | EXACT |
| 区块链 | blockchain | EXACT |
| 生物科技 | biotech | EXACT |
| 高端装备 | high_end_equipment | EXACT |
| 航空航天 | aerospace | EXACT |
| 新材料 | new_materials | EXACT |
| 新能源 | new_energy | EXACT |
| 金融科技 | fintech | EXACT |
| 纳米技术 | new_materials | MERGED — 纳米技术归入新材料 |

### 9.4 T4/T5: Seed Data → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| ai | ai | EXACT |
| quantum_computing | quantum_computing | EXACT |
| semiconductor | semiconductor | EXACT |
| biotech | biotech | EXACT |
| autonomous_driving | autonomous_driving | EXACT |
| new_materials | new_materials | EXACT |
| blockchain | blockchain | EXACT |
| high_end_equipment | high_end_equipment | EXACT |
| embodied_ai | embodied_ai | EXACT |
| auto_driving | autonomous_driving | SYNONYM |
| biotechnology | biotech | SYNONYM |
| new_energy | new_energy | EXACT |
| fintech | fintech | EXACT |

### 9.5 T6: Cleaning Service → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| ai | ai | EXACT |
| robotics | robotics | EXACT |
| quantum_computing | quantum_computing | EXACT |
| semiconductor | semiconductor | EXACT |
| autonomous_driving | autonomous_driving | EXACT |
| embodied_ai | embodied_ai | EXACT |
| biotech | biotech | EXACT |
| new_energy | new_energy | EXACT |
| new_materials | new_materials | EXACT |
| high_end_equipment | high_end_equipment | EXACT |

### 9.6 T7: Fixed Server → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| embodied_ai | embodied_ai | EXACT |
| auto_driving | autonomous_driving | SYNONYM |
| semiconductor | semiconductor | EXACT |
| ai | ai | EXACT |
| biotechnology | biotech | SYNONYM |
| quantum_computing | quantum_computing | EXACT |
| new_energy | new_energy | EXACT |
| fintech | fintech | EXACT |
| aerospace | aerospace | EXACT |
| advanced_manufacturing | high_end_equipment | MERGED |

### 9.7 T8: Landing Service → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| autonomous_driving | autonomous_driving | EXACT |
| embodied_ai | embodied_ai | EXACT |
| quantum_computing | quantum_computing | EXACT |

### 9.8 T9: Legacy Mock DB → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| ai_ml | ai | MERGED |
| biotech | biotech | EXACT |
| fintech | fintech | EXACT |
| cleantech | new_energy | MERGED |
| blockchain | blockchain | EXACT |

### 9.9 T10: Deeptech Schema (21) → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| ai_ml | ai | MERGED |
| robotics | robotics | EXACT |
| quantum_computing | quantum_computing | EXACT |
| biotech | biotech | EXACT |
| fintech | fintech | EXACT |
| cleantech | new_energy | MERGED |
| aerospace | aerospace | EXACT |
| semiconductor | semiconductor | EXACT |
| blockchain | blockchain | EXACT |
| vr_ar | vr_ar | EXACT |
| nanotech | new_materials | MERGED |
| space_tech | aerospace | MERGED |
| embodied_ai | embodied_ai | EXACT |
| autonomous_driving | autonomous_driving | EXACT |
| cybersecurity | cybersecurity | EXACT |
| iot | iot | EXACT |
| 5g | iot | MERGED — 5G 归入物联网 |
| edge_computing | iot | MERGED — 边缘计算归入物联网 |
| metaverse | vr_ar | MERGED — 元宇宙归入 VR/AR |
| web3 | blockchain | MERGED — Web3 归入区块链 |
| digital_twin | vr_ar | MERGED — 数字孪生归入 VR/AR |

### 9.10 T11: Evidence Graph Design → Canonical

| Legacy Value | Canonical ID | Confidence |
|---|---|---|
| AI | ai | EXACT |
| BIOTECH | biotech | EXACT |
| QUANTUM | quantum_computing | EXACT |
| CLEAN_TECH | new_energy | MERGED |
| ADVANCED_MATERIALS | new_materials | EXACT |
| OTHER | other | EXACT |

---

## 10. Ambiguous Mapping Rules

| Legacy Value | → Canonical | Rule | Reason |
|---|---|---|---|
| `ai_hardware` | `unknown` | 宁可 unknown | 无法确定归入 ai 还是 semiconductor |
| `auto_driving` | `autonomous_driving` | 同义词 | 明确指同一行业 |
| `biotechnology` | `biotech` | 同义词 | 明确指同一行业 |
| `ai_ml` | `ai` | 子领域归并 | ML 是 AI 的核心子领域 |
| `cleantech` | `new_energy` | 高度重叠 | 在 DeepTech 政策语境中高度重叠 |
| `nanotech` | `new_materials` | 子领域归并 | 纳米技术是新材料的子领域 |
| `space_tech` | `aerospace` | 高度重叠 | 航天航空与太空技术高度重叠 |
| `5g` | `iot` | 基础设施归并 | 5G 是 IoT 基础设施 |
| `edge_computing` | `iot` | 基础设施归并 | 边缘计算是 IoT 基础设施 |
| `metaverse` | `vr_ar` | 技术重叠 | 元宇宙依赖 VR/AR 技术 |
| `web3` | `blockchain` | 技术重叠 | Web3 基于区块链技术 |
| `digital_twin` | `vr_ar` | 技术重叠 | 数字孪生与 VR/AR 技术重叠 |
| `advanced_manufacturing` | `high_end_equipment` | 同义词 | 在政策语境中指同一类别 |

---

## 11. Unknown / Other Handling

**`unknown`**: 当 legacy value 无法可靠映射到任何 canonical ID 时使用。
- 示例: `ai_hardware` → `unknown`（可能属于 ai 或 semiconductor，但无可靠依据）

**`other`**: 当输入文本不包含任何已知行业关键词时的 fallback。
- 示例: Parser 遇到 "新材料" → 在 T1 中映射为 `other`；在 Canonical 中映射为 `new_materials`

**规则**:
- 不确定的映射 → `unknown`，不猜测
- 已确认的 fallback → `other`
- `unknown` 和 `other` 都不应出现在对外展示中

---

## 12–17. Component Impact Assessment

### 12. Parser Impact — **HIGH**

**当前**: `policy_cleaner.py` 使用 10 CN → 8 EN 映射  
**需要**: 更新映射使其输出 canonical IDs  
**风险**: 修改 Parser 核心逻辑可能影响所有下游  
**策略**: 新增 canonical mapping layer，不修改现有 Parser

### 13. Schema Impact — **MEDIUM**

**当前**: `IndustryType` enum 有 5 个值  
**需要**: 扩展为 16+ canonical IDs  
**风险**: 扩展 enum 是向后兼容的（新增值不影响旧值）  
**策略**: 扩展 enum，不删除现有值

### 14. Seed Data Impact — **MEDIUM**

**当前**: 两个 JSON 文件使用不同的 industry 标签  
**需要**: 通过 mapping table 映射到 canonical IDs  
**风险**: 直接修改 JSON 可能破坏现有引用  
**策略**: 不修改 JSON，在查询层提供 canonical 映射

### 15. Web Portal Impact — **LOW**

**当前**: 使用中文标签  
**需要**: 通过 mapping table 关联 canonical IDs  
**风险**: 低 — 仅展示层变化  
**策略**: 新增 CN→Canonical 映射表

### 16. API Impact — **LOW**

**当前**: API 接受 IndustryType enum 值  
**需要**: 扩展 enum 后 API 自动支持更多值  
**风险**: 向后兼容 — 旧值仍然有效  
**策略**: 扩展 enum，不修改 API contract

### 17. Evidence Graph Impact — **LOW**

**当前**: `sector` 为自由字符串  
**需要**: 可选择性地将 sector 映射到 canonical IDs  
**风险**: 极低 — 不影响 Trust Infrastructure  
**策略**: 保持兼容，未来可选迁移

---

## 18. Backward Compatibility

**策略**: 所有 legacy values 继续有效。Canonical IDs 是新增的规范层，不替换旧值。

```
Legacy Value → (mapping table) → Canonical ID

旧代码继续使用 legacy values
新代码推荐使用 canonical IDs
两者通过 mapping table 共存
```

---

## 19. Migration Strategy

**Phase 1 (P1-3.1 当前)**: Design — 建立 canonical registry 和 mapping matrix  
**Phase 2 (未来)**: Implement canonical registry as Python module  
**Phase 3 (未来)**: Add mapping layer to existing components  
**Phase 4 (未来)**: Gradually migrate new code to use canonical IDs  
**Phase 5 (远期)**: Deprecate legacy values (if ever needed)

**原则**: 渐进式迁移，每个 Phase 独立可回滚

---

## 20. Rollback Strategy

- Canonical registry 是独立模块，删除即可回滚
- Mapping tables 是只读数据，不影响现有逻辑
- 不修改任何现有数据文件
- 不删除任何现有 enum 值

---

## 21. Safety Constraints

**CONSTRAINT-001**: 不修改 Trust Score  
**CONSTRAINT-002**: 不修改 Provenance semantics  
**CONSTRAINT-003**: 不修改 Evidence Object contract  
**CONSTRAINT-004**: 不实现 MCP/A2A（MCP/A2A 为 future planned architecture，NOT IMPLEMENTED）  
**CONSTRAINT-005**: 不引入真实政府数据  
**CONSTRAINT-006**: 不删除旧 taxonomy  
**CONSTRAINT-007**: 不强制迁移现有数据  
**CONSTRAINT-008**: 不确定的映射必须保持 `unknown`

---

## 22. Open Questions

1. `ai_hardware` 应该归入 `ai` 还是 `semiconductor`？当前保持 `unknown`
2. `fintech` 是否属于 OpenInvest 核心 DeepTech 范围？
3. 是否需要支持未来新增行业？Registry 扩展流程是什么？
4. 是否需要采用国家标准行业分类（GB/T 4754）作为参考？
5. Evidence Graph 的 `sector` 字段是否应该迁移到 canonical IDs？

---

## 23. UNVERIFIED Items

| Item | Status | Notes |
|---|---|---|
| 21-category source | ✅ **VERIFIED** | `schemas/deeptech_policy_schema.json` L138-160, 21 enum values, file exists but no Python code references it |
| `ai_hardware` → canonical mapping | ⚠️ **UNVERIFIED** | 无法确定归入 ai 或 semiconductor |
| `fintech` 是否属于核心范围 | ⚠️ **UNVERIFIED** | 需要产品决策 |
| Canonical registry 最终数量 | ⚠️ **DESIGN PROPOSAL** | 16+2 是设计建议，非最终决定 |

---

## 24. 21-Category Provenance Investigation

**Status**: ✅ **VERIFIED**

**Source**: `global_policy_aggregator/schemas/deeptech_policy_schema.json`

**Evidence**:
- File exists at: `global_policy_aggregator/schemas/deeptech_policy_schema.json`
- Created in commit: `01ba935` (v3.1.0 Web Portal)
- Industry enum at lines 138-160
- Exactly 21 values: ai_ml, robotics, quantum_computing, biotech, fintech, cleantech, aerospace, semiconductor, blockchain, vr_ar, nanotech, space_tech, embodied_ai, autonomous_driving, cybersecurity, iot, 5g, edge_computing, metaverse, web3, digital_twin
- **No Python code references this schema file** — it appears to be a design-time schema definition

**Relationship to other taxonomies**:
- This 21-category schema is the **most expansive** taxonomy in the project
- Most of its values map cleanly to the proposed 16-category canonical registry
- 5 values (5g, edge_computing, metaverse, web3, digital_twin) are merged into broader categories

---

*Design Complete: 2026-08-26*  
*Implementation: NOT STARTED*  
*Quest: P1-3.1 STATUS: PASS*
