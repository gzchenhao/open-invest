"""
Global Policy Data Cleaning Service
数据清洗和管理服务，提供政策数据的验证、清洗和标准化功能
"""

import json
import logging
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sqlite3
from dataclasses import dataclass
import jieba
import jieba.posseg as pseg
from collections import Counter

from processors.policy_cleaner import PolicyCleaner, StructuredPolicy

logger = logging.getLogger(__name__)

@dataclass
class CleaningJob:
    """清洗任务"""
    job_id: str
    source_file: str
    status: str  # pending, processing, completed, failed
    created_at: str
    completed_at: Optional[str]
    policies_processed: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class CleaningReport:
    """清洗报告"""
    total_files: int
    processed_files: int
    total_policies: int
    successful_policies: int
    failed_policies: int
    cleaning_time_seconds: float
    error_summary: Dict[str, int]
    quality_metrics: Dict[str, Any]

class ChinaGovernmentDataCleaner:
    """中国政府红头文件和管委会公告数据清洗器"""
    
    def __init__(self):
        # 中国政府文件特征词库
        self.gov_keywords = {
            '发文机关': ['人民政府', '发改委', '科技局', '财政局', '人社局', '工信局', '商务局'],
            '文件类型': ['通知', '意见', '办法', '规定', '决定', '公告', '通告', '批复'],
            '政策特征': ['扶持', '补贴', '奖励', '优惠', '减免', '专项资金', '产业基金'],
            '金额单位': ['万元', '人民币', '元'],
            '时间格式': ['年', '月', '日', '日', '前', '以上', '以下'],
            '申报要求': ['申请', '申报', '提交', '材料', '资质', '条件', '要求']
        }
        
        # 行业分类关键词
        self.industry_keywords = {
            '人工智能': ['AI', '人工智能', '机器学习', '深度学习', '自然语言处理', '计算机视觉'],
            '自动驾驶': ['自动驾驶', '无人驾驶', '智能网联', '车联网', '智能汽车'],
            '半导体': ['半导体', '集成电路', '芯片', '晶圆', '微电子'],
            '量子计算': ['量子计算', '量子通信', '量子信息', '量子科技'],
            '区块链': ['区块链', '分布式', '加密货币', '智能合约'],
            '生物科技': ['生物科技', '生物医药', '基因', '疫苗', '生物制药'],
            '高端装备': ['高端装备', '智能制造', '工业机器人', '精密仪器'],
            '航空航天': ['航空航天', '航空', '航天', '卫星', '火箭'],
            '新材料': ['新材料', '纳米材料', '复合材料', '功能材料'],
            '新能源': ['新能源', '太阳能', '风能', '储能', '氢能'],
            '金融科技': ['金融科技', 'FinTech', '数字金融', '智能投顾']
        }
        
        # 初始化jieba分词
        jieba.initialize()

class DataCleaningService:
    """数据清洗服务"""
    
    def __init__(self, db_service, output_dir: str = "cleaned_data"):
        self.db_service = db_service
        self.cleaner = PolicyCleaner()
        self.china_cleaner = ChinaGovernmentDataCleaner()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jobs = {}
        
    def clean_china_government_documents(self, document_content: str, source_type: str = "government") -> StructuredPolicy:
        """专门处理中国政府红头文件和管委会公告"""
        try:
            # 文档类型识别
            doc_type = self._identify_document_type(document_content)
            
            # 提取关键信息
            extracted_info = self._extract_china_policy_info(document_content, doc_type)
            
            # 结构化转换
            structured_policy = self._convert_to_structured_policy(extracted_info, doc_type)
            
            # 中国特色标准化
            structured_policy = self._standardize_china_policy(structured_policy)
            
            return structured_policy
            
        except Exception as e:
            logger.error(f"Failed to clean China government document: {e}")
            raise
    
    def _identify_document_type(self, content: str) -> str:
        """识别中国政府文件类型"""
        # 红头文件特征
        if any(keyword in content for keyword in ['红头文件', '发文号', '文号', '签发人']):
            return "government_red_document"
        
        # 通知类文件
        if any(keyword in content for keyword in ['通知', '关于', '的', '通知']):
            return "government_notice"
        
        # 意见类文件
        if any(keyword in content for keyword in ['意见', '指导意见', '实施意见']):
            return "government_opinion"
        
        # 办法类文件
        if any(keyword in content for keyword in ['办法', '管理办法', '实施办法']):
            return "government_regulation"
        
        # 公告类文件
        if any(keyword in content for keyword in ['公告', '通告', '公示']):
            return "government_announcement"
        
        # 管委会文件
        if any(keyword in content for keyword in ['管委会', '管理委员会', '园区管委会']):
            return "park_document"
        
        return "unknown"
    
    def _extract_china_policy_info(self, content: str, doc_type: str) -> Dict[str, Any]:
        """提取中国政策关键信息"""
        info = {}
        
        # 提取发文机关
        info['issuing_authority'] = self._extract_issuing_authority(content)
        
        # 提取发文日期
        info['issue_date'] = self._extract_issue_date(content)
        
        # 提取政策标题
        info['title'] = self._extract_policy_title(content, doc_type)
        
        # 提取政策正文
        info['main_content'] = self._extract_main_content(content)
        
        # 提取激励措施
        info['incentives'] = self._extract_china_incentives(content)
        
        # 提取申请要求
        info['requirements'] = self._extract_china_requirements(content)
        
        # 提取申报流程
        info['application_process'] = self._extract_application_process(content)
        
        # 提取联系方式
        info['contact_info'] = self._extract_contact_info(content)
        
        # 提取有效期
        info['valid_period'] = self._extract_valid_period(content)
        
        return info
    
    def _extract_issuing_authority(self, content: str) -> str:
        """提取发文机关"""
        # 寻找常见的发文机关模式
        patterns = [
            r'([\u4e00-\u9fa5]{2,6}人民政府)',
            r'([\u4e00-\u9fa5]{2,6}发展和改革委员会)',
            r'([\u4e00-\u9fa5]{2,6}科学技术局)',
            r'([\u4e00-\u9fa5]{2,6}财政局)',
            r'([\u4e00-\u9fa5]{2,6}人力资源和社会保障局)',
            r'([\u4e00-\u9fa5]{2,6}工业和信息化局)',
            r'([\u4e00-\u9fa5]{2,6}商务局)',
            r'([\u4e00-\u9fa5]{2,6}高新区管委会)',
            r'([\u4e00-\u9fa5]{2,6}工业园区管委会)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "未知机关"
    
    def _extract_issue_date(self, content: str) -> str:
        """提取发文日期"""
        # 寻找日期模式
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'发布日期[:：](\d{4}年\d{1,2}月\d{1,2}日)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "未知日期"
    
    def _extract_policy_title(self, content: str, doc_type: str) -> str:
        """提取政策标题"""
        # 寻找标题模式
        title_patterns = [
            r'([\u4e00-\u9fa5]{2,20}政策)',
            r'([\u4e00-\u9fa5]{2,20}扶持办法)',
            r'([\u4e00-\u9fa5]{2,20}实施方案)',
            r'([\u4e00-\u9fa5]{2,20}管理办法)',
            r'([\u4e00-\u9fa5]{2,20}实施意见)',
            r'([\u4e00-\u9fa5]{2,20}奖励办法)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # 如果没有找到标准标题，取第一句话
        first_sentence = re.split(r'[。！？]', content)[0]
        if len(first_sentence) > 10:
            return first_sentence
        
        return "未知政策标题"
    
    def _extract_main_content(self, content: str) -> str:
        """提取政策正文"""
        # 移除红头文件格式信息
        cleaned_content = re.sub(r'发文号[:：].*?\n', '', content)
        cleaned_content = re.sub(r'签发人[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'文号[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'发布日期[:：].*?\n', '', cleaned_content)
        
        # 提取主要内容（去除开头和结尾的格式信息）
        lines = cleaned_content.split('\n')
        main_content = []
        
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^[一二三四五六七八九十]+、', line) and not re.match(r'^\d+\.', line):
                main_content.append(line)
        
        return '\n'.join(main_content)
    
    def _extract_china_incentives(self, content: str) -> List[Dict[str, Any]]:
        """提取中国政策激励措施 - 增强版"""
        incentives = []
        
        # 金额激励 - 增强版，重点采集具身智能/自动驾驶/半导体专项补贴、算力补贴、厂房租金优惠、人才奖励
        amount_patterns = [
            # 具身智能专项补贴
            r'具身智能\s*(\d+)\s*万元',
            r'具身智能\s*(\d+)\s*万',
            r'具身智能\s*补贴\s*(\d+)\s*万元',
            # 自动驾驶专项补贴
            r'自动驾驶\s*(\d+)\s*万元',
            r'自动驾驶\s*(\d+)\s*万',
            r'自动驾驶\s*补贴\s*(\d+)\s*万元',
            # 半导体专项补贴
            r'半导体\s*(\d+)\s*万元',
            r'半导体\s*(\d+)\s*万',
            r'集成电路\s*(\d+)\s*万元',
            r'芯片\s*(\d+)\s*万元',
            # 算力补贴
            r'算力补贴\s*(\d+)\s*万元',
            r'算力支持\s*(\d+)\s*万元',
            r'GPU补贴\s*(\d+)\s*万元',
            r'云计算\s*(\d+)\s*万元',
            # 厂房租金优惠
            r'厂房租金\s*(\d+)\s*年\s*免',
            r'办公场地\s*(\d+)\s*年\s*免租金',
            r'场地\s*(\d+)\s*年\s*免费',
            r'租金减免\s*(\d+)\s*%\s*或\s*(\d+)\s*年',
            # 人才奖励
            r'人才奖励\s*(\d+)\s*万元',
            r'高端人才\s*(\d+)\s*万元/年',
            r'专家津贴\s*(\d+)\s*万元/年',
            r'领军人才\s*(\d+)\s*万元',
            # 通用补贴模式
            r'补贴\s*(\d+)\s*万元',
            r'支持\s*(\d+)\s*万元',
            r'奖励\s*(\d+)\s*万元',
            r'资助\s*(\d+)\s*万元',
            r'最高\s*(\d+)\s*万元',
            r'不超过\s*(\d+)\s*万元'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                incentive_type = "财政补贴"
                if "具身智能" in pattern:
                    incentive_type = "具身智能专项补贴"
                elif "自动驾驶" in pattern:
                    incentive_type = "自动驾驶专项补贴"
                elif "半导体" in pattern:
                    incentive_type = "半导体专项补贴"
                elif "算力" in pattern:
                    incentive_type = "算力补贴"
                
                incentives.append({
                    "type": incentive_type,
                    "amount": int(match),
                    "unit": "万元",
                    "description": f"{incentive_type}{match}万元"
                })
        
        # 税收优惠
        tax_patterns = [
            r'企业所得税\s*(\d+)\s*年\s*全免',
            r'增值税\s*(\d+)\s*年\s*减免',
            r'税收\s*(\d+)\s*年\s*优惠',
            r'税收\s*(\d+)\s*年\s*返还',
            r'两免三减半',
            r'三免三减半'
        ]
        
        for pattern in tax_patterns:
            match = re.search(pattern, content)
            if match:
                if "两免三减半" in pattern:
                    incentives.append({
                        "type": "税收优惠",
                        "duration": "两免三减半",
                        "description": "企业所得税两免三减半"
                    })
                elif "三免三减半" in pattern:
                    incentives.append({
                        "type": "税收优惠",
                        "duration": "三免三减半",
                        "description": "企业所得税三免三减半"
                    })
                else:
                    incentives.append({
                        "type": "税收优惠",
                        "duration": match.group(1) + "年",
                        "description": f"税收优惠{match.group(1)}年"
                    })
        
        # 场地优惠 - 增强版
        location_patterns = [
            r'办公场地\s*(\d+)\s*年\s*免租金',
            r'厂房租金\s*(\d+)\s*年\s*减免',
            r'场地\s*(\d+)\s*年\s*免费',
            r'办公用房\s*(\d+)\s*年\s*补贴',
            r'研发场地\s*(\d+)\s*年\s*免费',
            r'厂房租金\s*(\d+)\s*折',
            r'租金减免\s*(\d+)\s*%'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                incentives.append({
                    "type": "场地优惠",
                    "duration": match.group(1) + "年",
                    "description": f"场地优惠{match.group(1)}年"
                })
        
        # 人才奖励 - 增强版
        talent_patterns = [
            r'高端人才\s*(\d+)\s*万元/年',
            r'专家津贴\s*(\d+)\s*万元/年',
            r'人才奖励\s*(\d+)\s*万元',
            r'引进补贴\s*(\d+)\s*万元',
            r'领军人才\s*(\d+)\s*万元',
            r'团队补贴\s*(\d+)\s*万元'
        ]
        
        for pattern in talent_patterns:
            match = re.search(pattern, content)
            if match:
                incentives.append({
                    "type": "人才奖励",
                    "amount": int(match.group(1)),
                    "unit": "万元/年",
                    "description": f"人才奖励{match.group(1)}万元/年"
                })
        
        # 算力补贴
        compute_patterns = [
            r'算力补贴\s*(\d+)\s*万元',
            r'算力支持\s*(\d+)\s*万元',
            r'计算资源\s*(\d+)\s*万元',
            r'GPU补贴\s*(\d+)\s*万元',
            r'云计算\s*(\d+)\s*万元'
        ]
        
        for pattern in compute_patterns:
            match = re.search(pattern, content)
            if match:
                incentives.append({
                    "type": "算力补贴",
                    "amount": int(match.group(1)),
                    "unit": "万元",
                    "description": f"算力补贴{match.group(1)}万元"
                })
        
        # 设备购置补贴
        equipment_patterns = [
            r'设备购置\s*(\d+)\s*万元',
            r'设备补贴\s*(\d+)\s*万元',
            r'研发设备\s*(\d+)\s*万元',
            r'仪器设备\s*(\d+)\s*万元'
        ]
        
        for pattern in equipment_patterns:
            match = re.search(pattern, content)
            if match:
                incentives.append({
                    "type": "设备购置补贴",
                    "amount": int(match.group(1)),
                    "unit": "万元",
                    "description": f"设备购置补贴{match.group(1)}万元"
                })
        
        return incentives
    
    def _extract_china_requirements(self, content: str) -> List[Dict[str, Any]]:
        """提取中国政策申请要求 - 增强版，重点采集研发人员比例/专利数量的硬性落地要求"""
        requirements = []
        
        # 研发人员比例要求 - 增强版，重点采集
        staff_patterns = [
            r'研发人员比例\s*不低于\s*(\d+)\s*%',
            r'研发人员\s*(\d+)\s*%\s*以上',
            r'研发人员占比\s*不低于\s*(\d+)\s*%',
            r'技术人员比例\s*不低于\s*(\d+)\s*%',
            r'技术人员\s*(\d+)\s*%\s*以上',
            r'研发团队\s*不低于\s*(\d+)\s*%',
            r'科技人员\s*不低于\s*(\d+)\s*%',
            r'研发人员\s*占比\s*达到\s*(\d+)\s*%'
        ]
        
        for pattern in staff_patterns:
            match = re.search(pattern, content)
            if match:
                requirements.append({
                    "type": "研发人员比例",
                    "percentage": match.group(1) + "%",
                    "description": f"研发人员比例不低于{match.group(1)}%"
                })
        
        # 专利数量要求 - 增强版，重点采集
        patent_patterns = [
            r'专利\s*(\d+)\s*项\s*以上',
            r'发明专利\s*(\d+)\s*项',
            r'发明专利\s*至少\s*(\d+)\s*项',
            r'知识产权\s*(\d+)\s*项',
            r'拥有\s*(\d+)\s*项\s*专利',
            r'核心专利\s*(\d+)\s*项',
            r'软件著作权\s*(\d+)\s*项',
            r'专利授权\s*(\d+)\s*项',
            r'授权专利\s*(\d+)\s*项'
        ]
        
        # 注册资本要求 - 增强版
        capital_patterns = [
            r'注册资本\s*(\d+)\s*万元以上',
            r'注册资金\s*(\d+)\s*万元以上',
            r'资本\s*(\d+)\s*万元以上',
            r'注册资本\s*不低于\s*(\d+)\s*万元',
            r'实缴资本\s*(\d+)\s*万元以上',
            r'企业规模\s*(\d+)\s*万元以上'
        ]
        
        for pattern in staff_patterns:
            match = re.search(pattern, content)
            if match:
                requirements.append({
                    "type": "研发人员比例",
                    "percentage": match.group(1) + "%",
                    "description": f"研发人员比例不低于{match.group(1)}%"
                })
        
        # 硬性落地要求 - 增强版
        landing_patterns = [
            r'必须\s*拥有\s*实际\s*场地',
            r'必须\s*具备\s*生产\s*能力',
            r'必须\s*建立\s*研发\s*中心',
            r'必须\s*落地\s*实施',
            r'必须\s*在本\s*地\s*注册',
            r'必须\s*在本\s*地\s*经营',
            r'必须\s*在本\s*地\s*纳税',
            r'必须\s*设立\s*独立\s*法人',
            r'必须\s*实际\s*投资\s*建设',
            r'必须\s*产生\s*实际\s*效益',
            r'必须\s*缴纳\s*社保\s*费用',
            r'必须\s*雇佣\s*本地\s*员工'
        ]
        
        # 专利数量要求 - 增强版，重点采集
        patent_patterns = [
            r'专利\s*(\d+)\s*项\s*以上',
            r'发明专利\s*(\d+)\s*项',
            r'发明专利\s*至少\s*(\d+)\s*项',
            r'知识产权\s*(\d+)\s*项',
            r'拥有\s*(\d+)\s*项\s*专利',
            r'核心专利\s*(\d+)\s*项',
            r'软件著作权\s*(\d+)\s*项',
            r'专利授权\s*(\d+)\s*项',
            r'授权专利\s*(\d+)\s*项'
        ]
        
        for pattern in patent_patterns:
            match = re.search(pattern, content)
            if match:
                patent_type = "专利数量"
                if "发明专利" in pattern:
                    patent_type = "发明专利数量"
                elif "软件著作权" in pattern:
                    patent_type = "软件著作权数量"
                
                requirements.append({
                    "type": patent_type,
                    "amount": int(match.group(1)),
                    "unit": "项",
                    "description": f"{patent_type}{match.group(1)}项以上"
                })
        
        # 硬性落地要求处理
        for pattern in landing_patterns:
            if re.search(pattern, content):
                requirements.append({
                    "type": "硬性落地要求",
                    "description": "必须满足项目落地要求"
                })
                break
        
        # 成立时间要求
        time_patterns = [
            r'成立\s*(\d+)\s*年以上',
            r'注册\s*(\d+)\s*年以上',
            r'运营\s*(\d+)\s*年以上',
            r'企业成立\s*(\d+)\s*年以上',
            r'注册时间\s*(\d+)\s*年以上'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content)
            if match:
                requirements.append({
                    "type": "成立时间",
                    "duration": match.group(1) + "年",
                    "description": f"成立时间{match.group(1)}年以上"
                })
        
        # 技术领域要求 - 增强版
        tech_patterns = [
            r'技术领域\s*：\s*([\u4e00-\u9fa5]+)',
            r'行业范围\s*：\s*([\u4e00-\u9fa5]+)',
            r'支持领域\s*：\s*([\u4e00-\u9fa5]+)',
            r'重点领域\s*：\s*([\u4e00-\u9fa5]+)',
            r'鼓励领域\s*：\s*([\u4e00-\u9fa5]+)',
            r'优先领域\s*：\s*([\u4e00-\u9fa5]+)'
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, content)
            if match:
                requirements.append({
                    "type": "技术领域",
                    "field": match.group(1),
                    "description": f"技术领域：{match.group(1)}"
                })
        
        # 硬性落地要求 - 增强版
        landing_patterns = [
            r'必须\s*拥有\s*实际\s*场地',
            r'必须\s*具备\s*生产\s*能力',
            r'必须\s*建立\s*研发\s*中心',
            r'必须\s*落地\s*实施',
            r'必须\s*在本\s*地\s*注册',
            r'必须\s*在本\s*地\s*经营',
            r'必须\s*在本\s*地\s*纳税',
            r'必须\s*设立\s*独立\s*法人',
            r'必须\s*实际\s*投资\s*建设',
            r'必须\s*产生\s*实际\s*效益',
            r'必须\s*缴纳\s*社保\s*费用',
            r'必须\s*雇佣\s*本地\s*员工'
        ]
        
        for pattern in landing_patterns:
            if re.search(pattern, content):
                requirements.append({
                    "type": "硬性落地要求",
                    "description": "必须满足项目落地要求"
                })
                break
        
        # 认证资质要求
        cert_patterns = [
            r'必须\s*通过\s*ISO\s*认证',
            r'必须\s*获得\s*资质\s*认证',
            r'必须\s*具备\s*相关\s*资质',
            r'必须\s*满足\s*行业\s*标准',
            r'必须\s*符合\s*国家\s*标准'
        ]
        
        for pattern in cert_patterns:
            if re.search(pattern, content):
                requirements.append({
                    "type": "认证资质",
                    "description": "必须满足相关认证资质要求"
                })
                break
        
        return requirements
    
    def _extract_application_process(self, content: str) -> List[str]:
        """提取申报流程"""
        process = []
        
        # 寻找申报步骤
        step_patterns = [
            r'(\d+)\s*、\s*([\u4e00-\u9fa5]+)',
            r'([一二三四五六七八九十]+)\s*、\s*([\u4e00-\u9fa5]+)',
            r'第\s*(\d+)\s*条\s*([\u4e00-\u9fa5]+)'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) >= 2:
                    process.append(f"{match[0]}、{match[1]}")
        
        return process[:5]  # 最多返回5个步骤
    
    def _extract_contact_info(self, content: str) -> Dict[str, str]:
        """提取联系方式"""
        contact = {}
        
        # 电话号码
        phone_patterns = [
            r'电话\s*[:：]\s*(\d{3,4}-\d{7,8})',
            r'联系电话\s*[:：]\s*(\d{3,4}-\d{7,8})',
            r'咨询电话\s*[:：]\s*(\d{3,4}-\d{7,8})',
            r'(\d{11})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, content)
            if match:
                contact['电话'] = match.group(1)
                break
        
        # 邮箱
        email_patterns = [
            r'邮箱\s*[:：]\s*([\w.-]+@[\w.-]+\.[\w]+)',
            r'电子邮箱\s*[:：]\s*([\w.-]+@[\w.-]+\.[\w]+)',
            r'联系邮箱\s*[:：]\s*([\w.-]+@[\w.-]+\.[\w]+)'
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, content)
            if match:
                contact['邮箱'] = match.group(1)
                break
        
        # 地址
        address_patterns = [
            r'地址\s*[:：]\s*([\u4e00-\u9fa5]+\s*[\u4e00-\u9fa5]+\s*[\u4e00-\u9fa5]+)',
            r'办公地址\s*[:：]\s*([\u4e00-\u9fa5]+\s*[\u4e00-\u9fa5]+\s*[\u4e00-\u9fa5]+)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, content)
            if match:
                contact['地址'] = match.group(1)
                break
        
        return contact
    
    def _extract_valid_period(self, content: str) -> str:
        """提取政策有效期"""
        period_patterns = [
            r'有效期\s*[:：]\s*(\d{4}年\d{1,2}月\d{1,2}日\s*至\s*\d{4}年\d{1,2}月\d{1,2}日)',
            r'执行期限\s*[:：]\s*(\d{4}年\d{1,2}月\d{1,2}日\s*至\s*\d{4}年\d{1,2}月\d{1,2}日)',
            r'有效期\s*(\d+)\s*年',
            r'有效期\s*(\d+)\s*个月'
        ]
        
        for pattern in period_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "长期有效"
    
    def _convert_to_structured_policy(self, extracted_info: Dict[str, Any], doc_type: str) -> StructuredPolicy:
        """将提取的信息转换为结构化政策"""
        # 创建结构化政策对象
        structured_policy = StructuredPolicy(
            policy_id=f"china_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(extracted_info['title']) % 10000}",
            location=extracted_info['issuing_authority'],
            country="中国",
            region=self._extract_region_from_authority(extracted_info['issuing_authority']),
            industry=self._identify_industry(extracted_info['main_content']),
            policy_type=self._map_policy_type(doc_type),
            title=extracted_info['title'],
            description=extracted_info['main_content'],
            incentives=extracted_info['incentives'],
            requirements=extracted_info['requirements'],
            compliance_standards=[],
            metadata={
                "document_type": doc_type,
                "issuing_authority": extracted_info['issuing_authority'],
                "issue_date": extracted_info['issue_date'],
                "valid_period": extracted_info['valid_period'],
                "contact_info": extracted_info['contact_info'],
                "application_process": extracted_info['application_process'],
                "source_type": "china_government"
            }
        )
        
        return structured_policy
    
    def _extract_region_from_authority(self, authority: str) -> str:
        """从发文机关提取地区信息"""
        # 常见地区映射
        region_mapping = {
            '北京': ['北京市', '北京'],
            '上海': ['上海市', '上海'],
            '广州': ['广州市', '广州'],
            '深圳': ['深圳市', '深圳'],
            '杭州': ['杭州市', '杭州'],
            '南京': ['南京市', '南京'],
            '成都': ['成都市', '成都'],
            '武汉': ['武汉市', '武汉'],
            '西安': ['西安市', '西安'],
            '天津': ['天津市', '天津'],
            '重庆': ['重庆市', '重庆'],
            '苏州': ['苏州市', '苏州'],
            '合肥': ['合肥市', '合肥']
        }
        
        for region, keywords in region_mapping.items():
            if any(keyword in authority for keyword in keywords):
                return region
        
        return "未知"
    
    def _identify_industry(self, content: str) -> str:
        """识别政策所属行业"""
        # 使用jieba分词进行关键词匹配
        words = jieba.cut(content)
        word_count = Counter(words)
        
        # 计算各行业关键词权重
        industry_scores = {}
        for industry, keywords in self.china_cleaner.industry_keywords.items():
            score = sum(word_count[keyword] for keyword in keywords)
            if score > 0:
                industry_scores[industry] = score
        
        # 返回得分最高的行业
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        
        return "其他"
    
    def _map_policy_type(self, doc_type: str) -> str:
        """映射政策类型"""
        type_mapping = {
            "government_red_document": "红头文件",
            "government_notice": "通知",
            "government_opinion": "意见",
            "government_regulation": "办法",
            "government_announcement": "公告",
            "park_document": "园区文件"
        }
        
        return type_mapping.get(doc_type, "其他")
    
    def _standardize_china_policy(self, policy: StructuredPolicy) -> StructuredPolicy:
        """标准化中国政策数据"""
        # 标准化激励措施
        standardized_incentives = []
        for incentive in policy.incentives:
            standardized_incentives.append({
                "type": incentive.get("type", ""),
                "amount": incentive.get("amount", 0),
                "unit": incentive.get("unit", ""),
                "duration": incentive.get("duration", ""),
                "description": incentive.get("description", "")
            })
        
        # 标准化申请要求
        standardized_requirements = []
        for requirement in policy.requirements:
            standardized_requirements.append({
                "type": requirement.get("type", ""),
                "amount": requirement.get("amount", 0),
                "unit": requirement.get("unit", ""),
                "percentage": requirement.get("percentage", ""),
                "duration": requirement.get("duration", ""),
                "field": requirement.get("field", ""),
                "description": requirement.get("description", "")
            })
        
        # 更新政策对象
        policy.incentives = standardized_incentives
        policy.requirements = standardized_requirements
        
        return policy
    
    def batch_clean_policies(self, source_files: List[str]) -> CleaningReport:
        """批量清洗政策文件"""
        import time
        
        start_time = time.time()
        total_files = len(source_files)
        processed_files = 0
        total_policies = 0
        successful_policies = 0
        failed_policies = 0
        error_summary = {}
        
        logger.info(f"Starting batch cleaning of {total_files} files")
        
        for file_path in source_files:
            try:
                job_id = f"clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(file_path).stem}"
                job = CleaningJob(
                    job_id=job_id,
                    source_file=file_path,
                    status="processing",
                    created_at=datetime.now().isoformat(),
                    completed_at=None
                )
                self.jobs[job_id] = job
                
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 判断是否为中国政府文件
                if self._is_china_government_document(content):
                    # 使用中国专用清洗器
                    structured_policy = self.clean_china_government_documents(content)
                else:
                    # 使用通用清洗器
                    structured_policy = self.cleaner.clean_policy_text(content, file_path)
                
                # 添加到数据库
                policy_id = self.db_service.add_policy(structured_policy)
                
                # 更新任务状态
                job.status = "completed"
                job.completed_at = datetime.now().isoformat()
                job.policies_processed = 1
                processed_files += 1
                total_policies += 1
                successful_policies += 1
                
                logger.info(f"Successfully cleaned policy from {file_path}: {policy_id}")
                
            except Exception as e:
                error_type = type(e).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
                
                # 更新任务状态
                if job_id in self.jobs:
                    self.jobs[job_id].status = "failed"
                    self.jobs[job_id].completed_at = datetime.now().isoformat()
                    self.jobs[job_id].errors.append(str(e))
                
                failed_policies += 1
                logger.error(f"Failed to clean policy from {file_path}: {e}")
        
        cleaning_time = time.time() - start_time
    
    def _is_china_government_document(self, content: str) -> bool:
        """判断是否为中国政府文件 - 增强版"""
        # 中国政府文件特征词
        gov_indicators = [
            '人民政府', '发改委', '科技局', '财政局', '人社局', '工信局', '商务局',
            '通知', '意见', '办法', '规定', '决定', '公告', '通告', '批复',
            '发文号', '文号', '签发人', '红头文件', '管委会', '园区',
            '扶持', '补贴', '奖励', '优惠', '减免', '专项资金', '产业基金',
            '申报', '申请', '材料', '资质', '条件', '要求'
        ]
        
        # 中国政府红头文件特征
        red_document_features = [
            '红头文件', '发文号', '文号', '签发人', '文件标题', '主送机关',
            '抄送机关', '主题词', '发文机关', '成文日期', '印发日期',
            '密级', '紧急程度', '份号', '序号'
        ]
        
        # 管委会文件特征
        park_document_features = [
            '管委会', '管理委员会', '园区管委会', '高新技术开发区',
            '经济技术开发区', '保税区', '出口加工区', '自由贸易区'
        ]
        
        # 计算匹配度
        gov_match_count = sum(1 for indicator in gov_indicators if indicator in content)
        red_doc_match_count = sum(1 for feature in red_document_features if feature in content)
        park_match_count = sum(1 for feature in park_document_features if feature in content)
        
        # 如果匹配度超过阈值，认为是政府文件
        if red_doc_match_count >= 2 or park_match_count >= 2:
            return True  # 明确是红头文件或管委会文件
        
        return gov_match_count >= 5
    
    def clean_chinese_red_document(self, document_content: str) -> StructuredPolicy:
        """专门处理中国政府红头文件 - 增强版"""
        try:
            # 提取红头文件特征信息
            red_doc_info = self._extract_red_document_features(document_content)
            
            # 清洗文档内容
            cleaned_content = self._clean_red_document_content(document_content)
            
            # 合并提取的信息
            combined_info = {
                **red_doc_info,
                'main_content': cleaned_content,
                'incentives': self._extract_china_incentives(cleaned_content),
                'requirements': self._extract_china_requirements(cleaned_content)
            }
            
            # 转换为结构化政策
            doc_type = "government_red_document" if red_doc_info.get('is_red_document') else "park_document"
            structured_policy = self._convert_to_structured_policy(combined_info, doc_type)
            
            # 添加红头文件特有信息
            structured_policy.metadata.update({
                'red_document_features': red_doc_info,
                'document_level': red_doc_info.get('document_level', '普通'),
                'issuing_authority': red_doc_info.get('issuing_authority', ''),
                'document_number': red_doc_info.get('document_number', ''),
                'issue_date': red_doc_info.get('issue_date', ''),
                'urgency_level': red_doc_info.get('urgency_level', '普通'),
                'chinese_government_features': self._identify_chinese_government_features(document_content)
            })
            
            # 中国特色标准化
            structured_policy = self._standardize_china_policy(structured_policy)
            
            return structured_policy
            
        except Exception as e:
            logger.error(f"Failed to clean Chinese red document: {e}")
            raise
    
    def _extract_red_document_features(self, content: str) -> Dict[str, Any]:
        """提取红头文件特征信息"""
        features = {}
        
        # 判断是否为红头文件
        features['is_red_document'] = any(keyword in content for keyword in ['红头文件', '发文号', '文号', '签发人'])
        
        # 提取文件级别
        if '特急' in content:
            features['document_level'] = '特急'
        elif '急' in content:
            features['document_level'] = '急件'
        else:
            features['document_level'] = '普通'
        
        # 提取紧急程度
        if '特急' in content:
            features['urgency_level'] = '特急'
        elif '急' in content:
            features['urgency_level'] = '急件'
        else:
            features['urgency_level'] = '普通'
        
        # 提取文号
        doc_number_patterns = [
            r'文号\s*[:：]\s*([A-Z0-9-]+)',
            r'发文号\s*[:：]\s*([A-Z0-9-]+)',
            r'文件编号\s*[:：]\s*([A-Z0-9-]+)'
        ]
        
        for pattern in doc_number_patterns:
            match = re.search(pattern, content)
            if match:
                features['document_number'] = match.group(1)
                break
        
        # 提取签发人
        signatory_patterns = [
            r'签发人\s*[:：]\s*([\u4e00-\u9fa5]{2,4})',
            r'签发\s*[:：]\s*([\u4e00-\u9fa5]{2,4})'
        ]
        
        for pattern in signatory_patterns:
            match = re.search(pattern, content)
            if match:
                features['signatory'] = match.group(1)
                break
        
        return features
    
    def _identify_chinese_government_features(self, content: str) -> Dict[str, Any]:
        """识别中国政府文件特征"""
        features = {
            'has_red_header': '红头文件' in content or '发文号' in content,
            'has_official_seal': '印章' in content or '公章' in content,
            'has_document_number': '文号' in content or '发文号' in content,
            'has_issuing_authority': False,
            'has_urgency_level': False,
            'has_confidentiality': False,
            'has_distribution_list': False,
            'government_level': 'unknown',
            'document_style': 'unknown'
        }
        
        # 识别发文机关级别
        if any(level in content for level in ['国务院', '中央', '国家', '全国']):
            features['government_level'] = 'national'
            features['has_issuing_authority'] = True
        elif any(level in content for level in ['省', '市', '区', '县']):
            features['government_level'] = 'local'
            features['has_issuing_authority'] = True
        elif '管委会' in content or '园区' in content:
            features['government_level'] = 'park'
            features['has_issuing_authority'] = True
        
        # 识别紧急程度
        if '特急' in content:
            features['has_urgency_level'] = True
            features['urgency_level'] = '特别紧急'
        elif '急' in content:
            features['has_urgency_level'] = True
            features['urgency_level'] = '紧急'
        
        # 识别密级
        if any(level in content for level in ['秘密', '机密', '绝密']):
            features['has_confidentiality'] = True
        
        # 识别分发范围
        if any(dist in content for dist in ['主送', '抄送', '分送']):
            features['has_distribution_list'] = True
        
        # 识别文件风格
        if '通知' in content and '意见' in content:
            features['document_style'] = 'regulatory'
        elif '办法' in content and '规定' in content:
            features['document_style'] = 'administrative'
        elif '实施意见' in content or '实施方案' in content:
            features['document_style'] = 'implementation'
        
        return features
    
    def _clean_red_document_content(self, content: str) -> str:
        """清洗红头文件内容"""
        # 移除红头文件格式信息
        cleaned_content = re.sub(r'发文号[:：].*?\n', '', content)
        cleaned_content = re.sub(r'签发人[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'文号[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'发布日期[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'主题词[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'主送机关[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'抄送机关[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'密级[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'紧急程度[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'份号[:：].*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'序号[:：].*?\n', '', cleaned_content)
        
        # 移除红头文件标识
        cleaned_content = re.sub(r'\s*[★☆]+\s*', '', cleaned_content)
        cleaned_content = re.sub(r'\s*【.*?】\s*', '', cleaned_content)
        
        # 清理多余的空行
        lines = cleaned_content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^[一二三四五六七八九十]+、', line) and not re.match(r'^\d+\.', line):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_chinese_policy_documents(self, document_paths: List[str]) -> Dict[str, Any]:
        """批量清洗中国政策文档"""
        results = {
            "total_files": len(document_paths),
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "policies_extracted": 0,
            "processing_time": 0,
            "errors": []
        }
        
        import time
        start_time = time.time()
        
        for file_path in document_paths:
            try:
                # 读取文档
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 清洗文档
                structured_policy = self.clean_china_government_documents(content)
                
                # 保存到数据库
                policy_id = self.db_service.add_policy(structured_policy)
                
                results["processed_files"] += 1
                results["successful_files"] += 1
                results["policies_extracted"] += 1
                
                logger.info(f"Successfully processed {file_path}: {policy_id}")
                
            except Exception as e:
                results["failed_files"] += 1
                results["errors"].append({
                    "file": file_path,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                logger.error(f"Failed to process {file_path}: {e}")
        
        results["processing_time"] = time.time() - start_time
        
        return results
        
        # 生成清洗报告
        report = CleaningReport(
            total_files=total_files,
            processed_files=processed_files,
            total_policies=total_policies,
            successful_policies=successful_policies,
            failed_policies=failed_policies,
            cleaning_time_seconds=cleaning_time,
            error_summary=error_summary,
            quality_metrics=self._calculate_quality_metrics()
        )
        
        # 保存报告
        self._save_cleaning_report(report)
        
        logger.info(f"Batch cleaning completed: {successful_policies}/{total_policies} policies successful")
        return report
    
    def validate_policy_data(self, policy_id: str) -> Dict[str, Any]:
        """验证政策数据质量"""
        try:
            policy = self.db_service.get_policy(policy_id)
            if not policy:
                return {"valid": False, "errors": ["Policy not found"]}
            
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "quality_score": 0.0,
                "completeness": {},
                "consistency": {}
            }
            
            # 检查必填字段
            required_fields = ["policy_id", "title", "country", "industry", "policy_type"]
            for field in required_fields:
                if not policy.get(field):
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["valid"] = False
            
            # 检查数据完整性
            completeness_checks = {
                "title": bool(policy.get("title")),
                "description": bool(policy.get("description") and len(policy.get("description", "")) > 50),
                "incentives": len(policy.get("incentives", [])) > 0,
                "requirements": len(policy.get("requirements", [])) > 0,
                "compliance_standards": len(policy.get("compliance_standards", [])) > 0,
                "metadata": bool(policy.get("metadata"))
            }
            
            validation_results["completeness"] = completeness_checks
            completeness_score = sum(completeness_checks.values()) / len(completeness_checks)
            
            # 检查数据一致性
            consistency_checks = {
                "industry_valid": policy.get("industry") in ["ai", "robotics", "quantum_computing", "biotech", "other"],
                "policy_type_valid": policy.get("policy_type") in ["tax_break", "subsidy", "grant", "other"],
                "confidence_score_valid": 0.0 <= policy.get("confidence_score", 0.0) <= 1.0
            }
            
            validation_results["consistency"] = consistency_checks
            consistency_score = sum(consistency_checks.values()) / len(consistency_checks)
            
            # 计算总体质量分数
            validation_results["quality_score"] = (completeness_score * 0.6 + consistency_score * 0.4)
            
            # 检查警告
            if policy.get("confidence_score", 0.0) < 0.5:
                validation_results["warnings"].append("Low confidence score")
            
            if len(policy.get("incentives", [])) == 0:
                validation_results["warnings"].append("No incentives found")
            
            if len(policy.get("requirements", [])) == 0:
                validation_results["warnings"].append("No requirements found")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate policy {policy_id}: {e}")
            return {"valid": False, "errors": [str(e)]}
    
    def standardize_policy_data(self, policy_id: str) -> Dict[str, Any]:
        """标准化政策数据"""
        try:
            policy = self.db_service.get_policy(policy_id)
            if not policy:
                return {"success": False, "error": "Policy not found"}
            
            # 标准化国家代码
            country_mapping = {
                "中国": "CN", "美国": "US", "欧盟": "EU", "新加坡": "SG",
                "日本": "JP", "韩国": "KR", "德国": "DE", "英国": "GB",
                "法国": "FR", "加拿大": "CA"
            }
            
            if policy.get("country") in country_mapping:
                policy["country"] = country_mapping[policy["country"]]
            
            # 标准化行业代码
            industry_mapping = {
                "人工智能": "ai", "机器人": "robotics", "量子计算": "quantum_computing",
                "生物技术": "biotech", "自动驾驶": "autonomous_driving", "区块链": "blockchain",
                "虚拟现实": "vr_ar", "增强现实": "vr_ar", "新材料": "other", "新能源": "other"
            }
            
            if policy.get("industry") in industry_mapping:
                policy["industry"] = industry_mapping[policy["industry"]]
            
            # 标准化政策类型
            policy_type_mapping = {
                "税收优惠": "tax_break", "财政补贴": "subsidy", "土地优惠": "land_grant",
                "专项资金": "grant", "贷款支持": "loan", "担保服务": "guarantee",
                "培训补贴": "training_grant", "研发税收抵免": "rtp_credit"
            }
            
            if policy.get("policy_type") in policy_type_mapping:
                policy["policy_type"] = policy_type_mapping[policy["policy_type"]]
            
            # 更新数据库
            self._update_policy_in_database(policy)
            
            return {"success": True, "policy_id": policy_id}
            
        except Exception as e:
            logger.error(f"Failed to standardize policy {policy_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def deduplicate_policies(self, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """去重政策"""
        try:
            with sqlite3.connect(self.db_service.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有政策
                cursor.execute("SELECT policy_id, title, description FROM policies")
                policies = cursor.fetchall()
                
                duplicates = []
                processed = set()
                
                for i, (policy_id_1, title_1, desc_1) in enumerate(policies):
                    if policy_id_1 in processed:
                        continue
                    
                    similar_policies = []
                    
                    for j, (policy_id_2, title_2, desc_2) in enumerate(policies[i+1:], i+1):
                        if policy_id_2 in processed:
                            continue
                        
                        # 计算相似度
                        similarity = self._calculate_similarity(title_1, title_2, desc_1, desc_2)
                        
                        if similarity >= similarity_threshold:
                            similar_policies.append({
                                "policy_id": policy_id_2,
                                "similarity": similarity,
                                "title": title_2,
                                "description": desc_2
                            })
                    
                    if similar_policies:
                        duplicates.append({
                            "original_policy": {
                                "policy_id": policy_id_1,
                                "title": title_1,
                                "description": desc_1
                            },
                            "similar_policies": similar_policies,
                            "similarity_threshold": similarity_threshold
                        })
                        
                        processed.add(policy_id_1)
                        for dup in similar_policies:
                            processed.add(dup["policy_id"])
                
                return duplicates
                
        except Exception as e:
            logger.error(f"Failed to deduplicate policies: {e}")
            return []
    
    def _calculate_similarity(self, title_1: str, title_2: str, desc_1: str, desc_2: str) -> float:
        """计算政策相似度"""
        try:
            # 简单的文本相似度计算
            def text_similarity(text1: str, text2: str) -> float:
                if not text1 or not text2:
                    return 0.0
                
                # 提取关键词
                words1 = set(re.findall(r'\b\w+\b', text1.lower()))
                words2 = set(re.findall(r'\b\w+\b', text2.lower()))
                
                if not words1 or not words2:
                    return 0.0
                
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                
                return len(intersection) / len(union)
            
            # 计算标题和描述的相似度
            title_sim = text_similarity(title_1, title_2)
            desc_sim = text_similarity(desc_1, desc_2)
            
            # 加权平均
            return (title_sim * 0.6 + desc_sim * 0.4)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """计算数据质量指标"""
        try:
            with sqlite3.connect(self.db_service.db_path) as conn:
                cursor = conn.cursor()
                
                # 总政策数
                cursor.execute("SELECT COUNT(*) FROM policies")
                total_policies = cursor.fetchone()[0]
                
                if total_policies == 0:
                    return {}
                
                # 平均置信度
                cursor.execute("SELECT AVG(confidence_score) FROM policies")
                avg_confidence = cursor.fetchone()[0] or 0.0
                
                # 高质量政策比例（置信度>0.8）
                cursor.execute("SELECT COUNT(*) FROM policies WHERE confidence_score > 0.8")
                high_quality_count = cursor.fetchone()[0]
                high_quality_ratio = high_quality_count / total_policies
                
                # 完整政策比例（有激励措施和要求）
                cursor.execute('''
                    SELECT COUNT(*) FROM policies 
                    WHERE incentives_json IS NOT NULL AND requirements_json IS NOT NULL
                ''' )
                complete_count = cursor.fetchone()[0]
                complete_ratio = complete_count / total_policies
                
                return {
                    "total_policies": total_policies,
                    "average_confidence_score": avg_confidence,
                    "high_quality_policy_ratio": high_quality_ratio,
                    "complete_policy_ratio": complete_ratio,
                    "data_quality_grade": self._get_quality_grade(avg_confidence, high_quality_ratio, complete_ratio)
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {e}")
            return {}
    
    def _get_quality_grade(self, confidence: float, high_quality_ratio: float, complete_ratio: float) -> str:
        """获取数据质量等级"""
        score = (confidence * 0.4 + high_quality_ratio * 0.3 + complete_ratio * 0.3)
        
        if score >= 0.8:
            return "A"
        elif score >= 0.6:
            return "B"
        elif score >= 0.4:
            return "C"
        else:
            return "D"
    
    def _save_cleaning_report(self, report: CleaningReport):
        """保存清洗报告"""
        report_file = self.output_dir / f"cleaning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.__dict__, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Cleaning report saved to {report_file}")
    
    def _update_policy_in_database(self, policy: Dict[str, Any]):
        """更新数据库中的政策"""
        try:
            with sqlite3.connect(self.db_service.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE policies SET
                        title = ?, location = ?, country = ?, region = ?, city = ?,
                        industry = ?, policy_type = ?, description = ?,
                        incentives_json = ?, requirements_json = ?, compliance_json = ?,
                        metadata_json = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE policy_id = ?
                ''', (
                    policy.get("title"),
                    policy.get("location"),
                    policy.get("country"),
                    policy.get("region"),
                    policy.get("city"),
                    policy.get("industry"),
                    policy.get("policy_type"),
                    policy.get("description"),
                    json.dumps(policy.get("incentives", []), ensure_ascii=False),
                    json.dumps(policy.get("requirements", []), ensure_ascii=False),
                    json.dumps(policy.get("compliance_standards", []), ensure_ascii=False),
                    json.dumps(policy.get("metadata", {}), ensure_ascii=False),
                    policy.get("policy_id")
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update policy in database: {e}")
            raise

# 使用示例
if __name__ == "__main__":
    # 创建数据库服务
    from .policy_database_service import PolicyDatabaseService
    
    db_service = PolicyDatabaseService()
    cleaning_service = DataCleaningService(db_service)
    
    # 示例政策文件列表
    sample_files = [
        "data/raw_policies/shanghai_ai_policy_2024.txt",
        "data/raw_policies/silicon_valley_quantum_policy_2024.txt",
        "data/raw_policies/eu_ai_act_compliance_2024.txt"
    ]
    
    # 批量清洗
    report = cleaning_service.batch_clean_policies(sample_files)
    print(f"Cleaning report: {report}")
    
    # 验证数据质量
    validation = cleaning_service.validate_policy_data("sample_policy_id")
    print(f"Validation result: {validation}")
    
    # 标准化数据
    standardization = cleaning_service.standardize_policy_data("sample_policy_id")
    print(f"Standardization result: {standardization}")
    
    # 去重检查
    duplicates = cleaning_service.deduplicate_policies()
    print(f"Found {len(duplicates)} duplicate groups")