#!/usr/bin/env python3
"""
TEST-VISION-001..004: Strategic Vision Alignment Tests
确保战略愿景与当前现实正确分离，防止误导性表述
"""

import re
import unittest
from pathlib import Path


class TestStrategicVisionAlignment(unittest.TestCase):
    """Strategic Vision Alignment 自动化测试"""
    
    def setUp(self):
        """测试初始化"""
        self.root_dir = Path(__file__).parent.parent
        self.readme_path = self.root_dir / "README.md"
        
    def test_vision_001_strategic_vision_presence(self):
        """TEST-VISION-001: 验证README包含战略愿景"""
        print("🔍 TEST-VISION-001: 验证README包含战略愿景")
        
        if not self.readme_path.exists():
            self.fail("README.md 文件不存在")
            
        content = self.readme_path.read_text(encoding='utf-8')
        
        # 验证包含"The USB-C for DeepTech"
        if "The USB-C for DeepTech" not in content:
            self.fail("TEST-VISION-001 失败: README.md 必须包含 'The USB-C for DeepTech'")
        
        print("✅ TEST-VISION-001 通过: README包含战略愿景")
    
    def test_vision_002_current_status_clarity(self):
        """TEST-VISION-002: 验证README包含当前状态明确表述"""
        print("🔍 TEST-VISION-002: 验证README包含当前状态表述")
        
        if not self.readme_path.exists():
            self.fail("README.md 文件不存在")
            
        content = self.readme_path.read_text(encoding='utf-8')
        
        # 验证包含明确的当前状态表述
        if "experimental framework" not in content.lower():
            self.fail("TEST-VISION-002 失败: README.md 必须包含 'experimental framework'")
        
        # 验证包含完整的句子
        if "OpenInvest is currently an experimental framework" not in content:
            self.fail("TEST-VISION-002 失败: 必须包含完整句子 'OpenInvest is currently an experimental framework'")
        
        print("✅ TEST-VISION-002 通过: README包含当前状态表述")
    
    def test_vision_003_no_misleading_identity_claims(self):
        """TEST-VISION-003: 验证没有误导性的身份宣称"""
        print("🔍 TEST-VISION-003: 验证没有误导性的身份宣称")
        
        if not self.readme_path.exists():
            self.fail("README.md 文件不存在")
            
        content = self.readme_path.read_text(encoding='utf-8')
        
        # 检查禁止的身份宣称
        forbidden_patterns = [
            r"OpenInvest is the USB-C for DeepTech",
            r"OpenInvest is.*USB-C.*DeepTech",
            r"We are.*USB-C.*DeepTech",
            r"OpenInvest.*the standard.*DeepTech",
            r"OpenInvest.*the universal.*DeepTech"
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.fail(f"TEST-VISION-003 失败: 发现误导性身份宣称: {pattern}")
        
        print("✅ TEST-VISION-003 通过: 无误导性身份宣称")
    
    def test_vision_004_mcp_a2a_future_references(self):
        """TEST-VISION-004: 验证MCP/A2A引用正确标记为未来架构"""
        print("🔍 TEST-VISION-004: 验证MCP/A2A引用正确标记")
        
        # 搜索所有相关文档
        search_paths = [
            self.root_dir / "README.md",
            self.root_dir / "docs",
            self.root_dir / "TASK-P0-2.3_Handover.md",
            self.root_dir / "docs" / "OpenInvest_Positioning_Framework.md"
        ]
        
        mcp_a2a_found = False
        proper_markers = ["planned", "future", "vision", "architecture", "direction", "planned architecture"]
        
        for search_path in search_paths:
            if search_path.is_file():
                content = search_path.read_text(encoding='utf-8', errors='ignore')
                
                # 检查MCP/A2A引用
                if any(term in content.lower() for term in ["mcp", "a2a", "agent-to-agent"]):
                    mcp_a2a_found = True
                    
                    # 验证有适当的未来标记
                    has_proper_marker = any(marker in content.lower() for marker in proper_markers)
                    if not has_proper_marker:
                        self.fail(f"TEST-VISION-004 失败: {search_path} 中的MCP/A2A引用缺少未来标记")
                        
            elif search_path.is_dir():
                # 递归搜索docs目录
                for md_file in search_path.rglob("*.md"):
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                    
                    if any(term in content.lower() for term in ["mcp", "a2a", "agent-to-agent"]):
                        mcp_a2a_found = True
                        
                        has_proper_marker = any(marker in content.lower() for marker in proper_markers)
                        if not has_proper_marker:
                            self.fail(f"TEST-VISION-004 失败: {md_file} 中的MCP/A2A引用缺少未来标记")
        
        if not mcp_a2a_found:
            print("⚠️  未发现MCP/A2A引用，测试通过（无引用需要验证）")
        else:
            print("✅ TEST-VISION-004 通过: MCP/A2A引用正确标记为未来架构")
    
    def test_vision_005_narrative_safety_check(self):
        """TEST-VISION-005: 验证投资者叙事安全性"""
        print("🔍 TEST-VISION-005: 验证投资者叙事安全性")
        
        narrative_guide = self.root_dir / "docs" / "Investor_Narrative_Guide.md"
        
        if not narrative_guide.exists():
            self.fail("TEST-VISION-005 失败: Investor_Narrative_Guide.md 不存在")
        
        content = narrative_guide.read_text(encoding='utf-8')
        
        # 验证包含必要的安全指导
        required_sections = [
            "Avoid",
            "Use", 
            "High-Risk Phrases to Avoid",
            "Safe and Honest Alternatives",
            "Risk Assessment Matrix"
        ]
        
        for section in required_sections:
            if section not in content:
                self.fail(f"TEST-VISION-005 失败: 缺少必要章节 '{section}'")
        
        print("✅ TEST-VISION-005 通过: 投资者叙事指南完整")


if __name__ == '__main__':
    unittest.main()