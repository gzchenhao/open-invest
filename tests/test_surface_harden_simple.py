#!/usr/bin/env python3
"""
TEST-SURFACE-001..004: Repository Surface Hardening 防回归测试
确保治理效果的持续性，防止新增未标识的虚构政府联系方式
"""

import os
import re
import json
import unittest
from pathlib import Path
from typing import List, Dict, Any

class TestSurfaceHardening(unittest.TestCase):
    """Repository Surface Hardening 自动化防回归测试"""
    
    def setUp(self):
        """测试初始化"""
        self.root_dir = Path(__file__).parent.parent
        self.h2_files = [
            "global_policy_aggregator/agents/policy_ai_agent.py",
            "global_policy_aggregator/data/raw_policies/shanghai_ai_policy_2024.txt", 
            "global_policy_aggregator/scripts/update_policy_data.py",
            "global_policy_aggregator/test_frontend_data.html",
            "policy_crawler/crawlers/china_crawler.py",
            "policy_crawler/data/raw_policies/sample_shanghai_policy.txt",
            "policy_crawler/data/raw_policies/shanghai_ai_policy.txt",
            "policy_crawler/data/raw_policies/shanghai_policies_sample.json",
            "policy_crawler/data/raw_policies/shanghai_pudong_ai_policy.txt",
            "policy_crawler/data/raw_policies/shanghai_quantum_policy.txt",
            "policy_crawler/data/structured_policies/shanghai-qingpu-ai-hub-2024.json",
            "policy_crawler/data/structured_policies/shanghai_policy_structured.json",
            "policy_crawler/data/structured_policies/shenzhen-special-economic-zone-ai-policy-2024.json"
        ]
        self.contact_pattern = r'(电话|电话号码|联系电话|contact|phone|tel):\s*[\d-]+'
        self.email_pattern = r'(邮箱|email):\s*[\w\.-]+@[\w\.-]+'
        
    def test_surface_harden_001_mock_identification(self):
        """TEST-SURFACE-001: H2文件MOCK标识检查"""
        print("TEST-SURFACE-001: H2文件MOCK标识检查")
        
        mock_missing = []
        for file_path in self.h2_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            # 检查是否包含MOCK标识
            has_mock_header = "MOCK DATA" in content.upper() or "MOCK" in content[:500]
            has_mock_comment = "# MOCK" in content or "// MOCK" in content or "<!-- MOCK -->" in content
            has_mock_metadata = '"mock_metadata":' in content if file_path.endswith('.json') else False
            
            # 对于Python文件，检查是否包含MOCK声明
            if file_path.endswith('.py'):
                has_mock_declaration = "MOCK DATA" in content[:300] or "DEMONSTRATION DATA" in content[:300]
                if not (has_mock_header or has_mock_declaration):
                    mock_missing.append(file_path)
            
            # 对于HTML文件，检查是否包含MOCK标识
            elif file_path.endswith('.html'):
                html_mock_indicators = ["MOCK DATA", "MOCK", "DEMONSTRATION DATA", "重要声明：MOCK数据演示"]
                has_html_mock = any(indicator in content for indicator in html_mock_indicators)
                if not has_html_mock:
                    mock_missing.append(file_path)
            
            # 对于JSON文件，检查是否包含mock_metadata
            elif file_path.endswith('.json'):
                if not has_mock_metadata:
                    mock_missing.append(file_path)
            
            # 对于文本文件，检查是否包含MOCK声明
            elif file_path.endswith('.txt'):
                if not has_mock_header:
                    mock_missing.append(file_path)
        
        if mock_missing:
            print(f"ERROR: 以下文件缺少MOCK标识: {mock_missing}")
            self.fail(f"TEST-SURFACE-001 失败: {len(mock_missing)} 个文件缺少MOCK标识")
        else:
            print("SUCCESS: TEST-SURFACE-001 通过: 所有H2文件均包含MOCK标识")
    
    def test_surface_harden_002_unverified_url_markers(self):
        """TEST-SURFACE-002: Crawler URL UNVERIFIED标记检查"""
        print("TEST-SURFACE-002: Crawler URL UNVERIFIED标记检查")
        
        crawler_files = [
            "policy_crawler/crawlers/china_crawler.py",
            "policy_crawler/mock_policy_database.py", 
            "policy_crawler/processors/mock_policy_database.py"
        ]
        
        unverified_missing = []
        for file_path in crawler_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            # 检查是否包含UNVERIFIED说明
            has_unverified = "UNVERIFIED" in content.upper()
            if not has_unverified:
                unverified_missing.append(file_path)
        
        if unverified_missing:
            print(f"ERROR: 以下文件缺少UNVERIFIED标记: {unverified_missing}")
            self.fail(f"TEST-SURFACE-002 失败: {len(unverified_missing)} 个文件缺少UNVERIFIED标记")
        else:
            print("SUCCESS: TEST-SURFACE-002 通过: 所有Crawler文件均包含UNVERIFIED标记")
    
    def test_surface_harden_03_harmful_contact_validation(self):
        """TEST-SURFACE-003: 危害性联系方式检查"""
        print("TEST-SURFACE-003: 危害性联系方式检查")
        
        harmful_contacts = []
        for file_path in self.h2_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            # 检查是否存在未标记的危害性联系方式
            phone_matches = re.findall(self.contact_pattern, content)
            email_matches = re.findall(self.email_pattern, content)
            
            # 如果包含联系方式但缺少MOCK标识，则认为是危害性
            if (phone_matches or email_matches) and "MOCK" not in content[:1000]:
                harmful_contacts.append({
                    'file': file_path,
                    'phones': [match[1] for match in phone_matches],
                    'emails': [match[1] for match in email_matches]
                })
        
        if harmful_contacts:
            print("ERROR: 发现未标记的危害性联系方式:")
            for contact in harmful_contacts:
                print(f"  文件: {contact['file']}")
                print(f"    电话: {contact['phones']}")
                print(f"    邮箱: {contact['emails']}")
            self.fail(f"TEST-SURFACE-003 失败: 发现 {len(harmful_contacts)} 个文件包含未标记的危害性联系方式")
        else:
            print("SUCCESS: TEST-SURFACE-003 通过: 未发现未标记的危害性联系方式")
    
    def test_surface_harden_04_misleading_content_detection(self):
        """TEST-SURFACE-004: 误导性内容检查"""
        print("TEST-SURFACE-004: 误导性内容检查")
        
        misleading_keywords = [
            "official", "政府", "政策", "官方网站", "官方联系方式",
            "真实数据", "真实政策", "正式发布", "正式文件"
        ]
        
        misleading_found = []
        for file_path in self.h2_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            # 检查是否包含误导性关键词且缺少MOCK标识
            content_lower = content.lower()
            found_keywords = [kw for kw in misleading_keywords if kw.lower() in content_lower]
            
            # 对于不同文件类型检查MOCK标识
            if file_path.endswith('.json'):
                has_mock_metadata = '"mock_metadata":' in content
                has_mock_decl = "MOCK" in content[:500]
            elif file_path.endswith('.html'):
                html_mock_indicators = ["MOCK DATA", "MOCK", "DEMONSTRATION DATA", "重要声明：MOCK数据演示"]
                has_mock_decl = any(indicator in content for indicator in html_mock_indicators)
            else:
                has_mock_metadata = False
                has_mock_decl = "MOCK" in content[:500]
            
            if found_keywords and not (has_mock_metadata or has_mock_decl):
                misleading_found.append({
                    'file': file_path,
                    'keywords': found_keywords
                })
        
        if misleading_found:
            print("ERROR: 发现可能误导性内容:")
            for item in misleading_found:
                print(f"  文件: {item['file']}")
                print(f"    关键词: {item['keywords']}")
            self.fail(f"TEST-SURFACE-004 失败: 发现 {len(misleading_found)} 个文件包含可能误导性内容")
        else:
            print("SUCCESS: TEST-SURFACE-004 通过: 未发现误导性内容")

def main():
    """运行所有测试"""
    print("=" * 60)
    print("TEST-SURFACE-001..004: Repository Surface Hardening 防回归测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSurfaceHardening)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"总测试数: {result.testsRun}")
    print(f"成功数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    
    if result.failures:
        print("\n失败详情:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n错误详情:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # 返回测试状态
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)