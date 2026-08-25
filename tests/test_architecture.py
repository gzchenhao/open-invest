#!/usr/bin/env python3
"""
TEST-ARCH-001..004: Trust Infrastructure Architecture Tests
验证OpenInvest信任架构文档的正确性和完整性
"""

import re
import unittest
from pathlib import Path


class TestTrustInfrastructureArchitecture(unittest.TestCase):
    """Trust Infrastructure Architecture 自动化测试"""
    
    def setUp(self):
        """测试初始化"""
        self.root_dir = Path(__file__).parent.parent
        self.docs_dir = self.root_dir / "docs"
        self.expected_docs = [
            "OpenInvest_Core_Thesis.md",
            "OpenInvest_Trust_Architecture.md", 
            "Policy_Evidence_Graph.md",
            "Agent_Trust_Model.md",
            "MCP_A2A_Future_Architecture.md",
            "DeepTech_Agent_Economy_Positioning.md"
        ]
        
    def test_arch_001_architecture_docs_exist(self):
        """TEST-ARCH-001: 验证架构文档存在"""
        print("🔍 TEST-ARCH-001: 验证架构文档存在")
        
        missing_docs = []
        for doc_name in self.expected_docs:
            doc_path = self.docs_dir / doc_name
            if not doc_path.exists():
                missing_docs.append(doc_name)
                
        if missing_docs:
            print(f"❌ 缺少文档: {missing_docs}")
            self.fail(f"TEST-ARCH-001 失败: 缺少 {len(missing_docs)} 个架构文档")
        else:
            print("✅ TEST-ARCH-001 通过: 所有架构文档存在")
    
    def test_arch_002_mcp_a2a_future_references(self):
        """TEST-ARCH-002: 验证所有MCP/A2A引用都是未来/计划中的"""
        print("🔍 TEST-ARCH-002: 验证MCP/A2A引用标记")
        
        # 合适的标记词汇
        proper_markers = [
            "future", "planned", "vision", "architecture", "design", 
            "blueprint", "concept", "proposed", "intended", "roadmap",
            "planned architecture", "future integration", "future direction"
        ]
        
        # 不合适的表述
        problematic_terms = [
            "implemented", "building", "deployed", "active", "running",
            "working", "functional", "operational", "completed"
        ]
        
        issues_found = []
        
        for doc_name in self.expected_docs:
            doc_path = self.docs_dir / doc_name
            if not doc_path.exists():
                continue
                
            content = doc_path.read_text(encoding='utf-8')
            
            # 检查MCP/A2A相关术语
            mcp_a2a_pattern = r'(MCP|A2A|agent-to-agent|agent interoperability)'
            matches = re.finditer(mcp_a2a_pattern, content, re.IGNORECASE)
            
            for match in matches:
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]
                
                # 检查是否有合适的标记
                has_proper_marker = any(marker in context.lower() for marker in proper_markers)
                has_problematic_term = any(term in context.lower() for term in problematic_terms)
                
                if not has_proper_marker and has_problematic_term:
                    issues_found.append({
                        'doc': doc_name,
                        'term': match.group(),
                        'issue': f'MCP/A2A引用缺少未来标记'
                    })
        
        if issues_found:
            print("❌ 发现MCP/A2A引用标记问题:")
            for issue in issues_found:
                print(f"  文档: {issue['doc']}")
                print(f"    术语: {issue['term']}")
                print(f"    问题: {issue['issue']}")
            self.fail(f"TEST-ARCH-002 失败: 发现 {len(issues_found)} 个MCP/A2A引用标记问题")
        else:
            print("✅ TEST-ARCH-002 通过: 所有MCP/A2A引用都有合适的未来标记")
    
    def test_arch_003_no_mcp_a2a_implementation_claim(self):
        """TEST-ARCH-003: 验证没有文档声称实现了MCP/A2A"""
        print("🔍 TEST-ARCH-003: 验证没有MCP/A2A实现声称")
        
        # 禁止的实现声称表述
        forbidden_patterns = [
            r"we have implemented.*MCP",
            r"MCP.*is implemented", 
            r"we built.*A2A",
            r"A2A.*is functional",
            r"agent interoperability.*works",
            r"MCP/A2A.*integration.*complete",
            r"we deployed.*MCP",
            r"MCP.*system.*live"
        ]
        
        issues_found = []
        
        for doc_name in self.expected_docs:
            doc_path = self.docs_dir / doc_name
            if not doc_path.exists():
                continue
                
            content = doc_path.read_text(encoding='utf-8')
            
            for pattern in forbidden_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues_found.append({
                        'doc': doc_name,
                        'pattern': pattern,
                        'match': match.group()
                    })
        
        if issues_found:
            print("❌ 发现MCP/A2A实现声称:")
            for issue in issues_found:
                print(f"  文档: {issue['doc']}")
                print(f"    模式: {issue['pattern']}")
                print(f"    匹配: {issue['match']}")
            self.fail(f"TEST-ARCH-003 失败: 发现 {len(issues_found)} 个MCP/A2A实现声称")
        else:
            print("✅ TEST-ARCH-003 通过: 没有文档声称实现了MCP/A2A")
    
    def test_arch_004_trust_layer_terminology(self):
        """TEST-ARCH-004: 验证Trust Layer术语存在"""
        print("🔍 TEST-ARCH-004: 验证Trust Layer术语存在")
        
        # 必须存在的信任层相关术语
        required_terms = [
            "trust layer",
            "trust infrastructure", 
            "trust framework",
            "trust model",
            "evidence layer",
            "provenance layer",
            "verification layer"
        ]
        
        missing_terms = []
        
        for doc_name in self.expected_docs:
            doc_path = self.docs_dir / doc_name
            if not doc_path.exists():
                continue
                
            content = doc_path.read_text(encoding='utf-8')
            content_lower = content.lower()
            
            # 检查每个必需术语是否在文档中
            for term in required_terms:
                if term not in content_lower:
                    missing_terms.append({
                        'doc': doc_name,
                        'term': term
                    })
                    break  # 只要有一个术语缺失就标记该文档有问题
        
        if missing_terms:
            print("❌ 信任层术语缺失:")
            for missing in missing_terms:
                print(f"  文档: {missing['doc']}")
                print(f"    缺少术语: {missing['term']}")
            self.fail(f"TEST-ARCH-004 失败: {len(missing_terms)} 个文档缺少信任层术语")
        else:
            print("✅ TEST-ARCH-004 通过: 所有文档都包含信任层术语")


if __name__ == '__main__':
    unittest.main()