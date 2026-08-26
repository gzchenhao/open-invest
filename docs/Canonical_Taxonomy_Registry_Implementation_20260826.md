# Canonical Taxonomy Registry — Implementation Documentation

**Document**: `Canonical_Taxonomy_Registry_Implementation_20260826.md`  
**Quest**: P1-3.2 — Implement Canonical Taxonomy Registry and Legacy Mapping Layer  
**Type**: IMPLEMENTATION  
**Date**: 2026-08-26  
**Depends on**: P1-3.1 Design (`Industry_Taxonomy_Alignment_Design.md`)  
**Status**: ✅ IMPLEMENTED · REGISTRY + MAPPING LAYER ACTIVE  

---

## 1. Canonical Taxonomy

OpenInvest Canonical Taxonomy Registry 是项目中行业分类的 **single source of truth**。

当前版本包含 **16 个 active canonical categories** + `other` + `unknown` = **18 slots**。

这不是"唯一正确的行业分类"，而是 **OpenInvest canonical taxonomy proposal/registry**——一个经过审计、可验证、可回滚的提案。

---

## 2. Canonical IDs

| # | Canonical ID | 中文名称 | English Name |
|---:|---|---|---|
| 1 | `ai` | 人工智能 | Artificial Intelligence |
| 2 | `robotics` | 机器人 | Robotics |
| 3 | `embodied_ai` | 具身智能 | Embodied AI |
| 4 | `quantum_computing` | 量子计算 | Quantum Computing |
| 5 | `semiconductor` | 半导体 | Semiconductor |
| 6 | `biotech` | 生物医药 | Biotechnology |
| 7 | `autonomous_driving` | 自动驾驶 | Autonomous Driving |
| 8 | `aerospace` | 航空航天 | Aerospace & Defense |
| 9 | `new_energy` | 新能源 | New Energy & CleanTech |
| 10 | `new_materials` | 新材料 | Advanced Materials |
| 11 | `blockchain` | 区块链 | Blockchain & Web3 |
| 12 | `fintech` | 金融科技 | FinTech |
| 13 | `high_end_equipment` | 高端装备 | Advanced Manufacturing |
| 14 | `cybersecurity` | 网络安全 | Cybersecurity |
| 15 | `iot` | 物联网 | Internet of Things |
| 16 | `vr_ar` | 虚拟现实/增强现实 | VR/AR & Metaverse |
| — | `other` | 其他 | Other |
| — | `unknown` | 未知 | Unknown |

---

## 3. Legacy Sources

Registry 追踪 **10 个 legacy taxonomy sources**：

| Source ID | File | Count | Status |
|---|---|---:|---|
| T1_parser | `policy_cleaner.py` | 8 | Active |
| T2_schema | `schema/types.py` | 5 | Active |
| T3_web_portal | `interactive_ai_server.py` | 12 | Active |
| T4_seed_data | `china_policy_seed_data.json` + `detailed_china_tech_policies.json` | 13 | Active |
| T6_cleaning_service | `china_policy_cleaning_service.py` | 10 | Active |
| T7_fixed_server | `fixed_server.py` | 10 | Active |
| T8_landing_service | `landing_requirements_service.py` | 3 | Active |
| T9_legacy_mock_db | `policy_crawler/processors/mock_policy_database.py` | 5 | Legacy |
| T10_deeptech_schema | `schemas/deeptech_policy_schema.json` | 21 | Unused |
| T11_evidence_graph | `docs/Evidence_Graph_Prototype.md` | 6 | Design |

---

## 4. Mapping Rules

### Confidence Levels

| Level | Meaning | Example |
|---|---|---|
| `EXACT` | 完全相同的字符串 | `ai` → `ai` |
| `SYNONYM` | 明确同义词 | `auto_driving` → `autonomous_driving` |
| `NORMALIZATION` | 大小写/格式归一化 | `AI` → `ai` |
| `SEMANTIC_MAPPING` | 语义归并（有据可查） | `5g` → `iot` |
| `UNKNOWN` | 无法可靠判断 | `ai_hardware` → `unknown` |
| `OTHER` | 已确认行业但不在 canonical 中 | (parser fallback) → `other` |

### Key Mappings

- `biotech` ↔ `biotechnology` → `biotech` (SYNONYM)
- `autonomous_driving` ↔ `auto_driving` → `autonomous_driving` (SYNONYM)
- `ai_ml` → `ai` (NORMALIZATION)
- `cleantech` → `new_energy` (NORMALIZATION)
- `nanotech` → `new_materials` (SEMANTIC_MAPPING)
- `space_tech` → `aerospace` (SEMANTIC_MAPPING)
- `5g` / `edge_computing` → `iot` (SEMANTIC_MAPPING)
- `metaverse` / `digital_twin` → `vr_ar` (SEMANTIC_MAPPING)
- `web3` → `blockchain` (SEMANTIC_MAPPING)
- `ai_hardware` → `unknown` (UNKNOWN — 无法确定归入 ai 或 semiconductor)

---

## 5. UNKNOWN Semantics

**`unknown`** 表示：无法可靠判断应该属于哪个 canonical category。

使用场景：
- `ai_hardware`：可能属于 ai 或 semiconductor，但无可靠依据
- 完全无法识别的行业字符串
- 空值或 None

**原则**：宁可 unknown，不要猜测。

---

## 6. OTHER Semantics

**`other`** 表示：已确认属于 DeepTech/industry taxonomy，但不属于当前 canonical registry 的任何具体类别。

使用场景：
- Parser 遇到已知行业关键词但不在映射表中
- 确认是行业分类但无法归入 16 个具体类别

**与 unknown 的区别**：
- `other` = 确认是行业，只是不在具体类别中
- `unknown` = 无法可靠判断是什么

---

## 7. Backward Compatibility

**所有 legacy values 继续有效。**

- 现有 Parser 不需要修改即可继续工作
- 现有 Seed Data 不需要修改
- 现有 Web Portal 不需要修改
- 现有 Schema enum 不需要修改

Registry 是一个 **新增的独立层**，通过 `resolve()` 方法提供 legacy → canonical 映射。

---

## 8. Parser Integration

当前两个 Parser 保持独立运行：

1. `policy_cleaner.py` — 10 CN → 8 EN
2. `china_policy_cleaning_service.py` — 10 CN → 10 EN

Registry 不修改这两个 Parser。未来可以通过以下方式集成：

```python
from schema.canonical_taxonomy import get_registry

registry = get_registry()
parser_output = "ai"  # from policy_cleaner
canonical_id = registry.resolve(parser_output)  # → "ai"
```

---

## 9. API Impact

**当前无 API breaking change。**

Registry 是内部模块，不改变任何 API contract。

未来可选扩展：
- API 响应中增加 `canonical_industry` 字段
- API 接受 canonical ID 作为查询参数
- 保持旧字段向后兼容

---

## 10. Data Migration Policy

**本阶段不执行任何数据迁移。**

- 不修改 Seed Data JSON 文件
- 不修改 Web Portal mock 数据
- 不修改数据库记录
- 不重写历史数据

未来迁移策略（如需要）：
1. 在查询层提供 canonical mapping
2. 新数据推荐使用 canonical IDs
3. 旧数据通过 mapping table 保持可解释

---

## 11. Future Evolution Policy

- 新增 canonical category 需要在 Registry 中添加条目
- 新增 legacy source 需要在 `_LEGACY_SOURCES` 中注册
- 所有映射变更必须有测试覆盖
- 不允许删除已有 canonical ID
- 不允许修改已有 canonical ID 的语义

---

## Implementation Files

| File | Purpose |
|---|---|
| `schema/canonical_taxonomy.py` | Canonical Industry Registry + Legacy Mapping Layer |
| `tests/test_canonical_taxonomy.py` | 66 implementation tests |
| `docs/Industry_Taxonomy_Alignment_Design.md` | P1-3.1 design document |
| `docs/Industry_Taxonomy_Audit_20260826.md` | P1-3.0 audit document |

---

*Implementation Complete: 2026-08-26*  
*Tests: 282 passed, 0 failed (+66 new)*  
*Quest: P1-3.2 STATUS: PASS*
