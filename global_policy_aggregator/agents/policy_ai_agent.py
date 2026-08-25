"""
Global Policy AI Agent
AI智能政策助手，提供智能政策推荐、申请指导和合规检查功能

=============================================
⚠️  重要声明：MOCK数据 ⚠️
=============================================
本文件包含虚构的政府联系方式、政策数据和示例内容。
所有数据均为演示和测试用途，不代表任何真实的政府政策。

包含的虚构联系方式示例：
- 021-12345678 (上海市经济发展局)
- contact@example.com

请勿误认为真实的政府联系方式。
=============================================
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from services.policy_database_service import PolicyDatabaseService, PolicyQueryFilter
from services.data_cleaning_service import DataCleaningService
from processors.policy_cleaner import PolicyCleaner

logger = logging.getLogger(__name__)

class AgentActionType(Enum):
    """AI Agent动作类型"""
    POLICY_SEARCH = "policy_search"
    POLICY_RECOMMENDATION = "policy_recommendation"
    APPLICATION_GUIDANCE = "application_guidance"
    COMPLIANCE_CHECK = "compliance_check"
    ELIGIBILITY_ASSESSMENT = "eligibility_assessment"
    BENEFIT_CALCULATION = "benefit_calculation"
    DOCUMENT_GENERATION = "document_generation"
    FOLLOWUP_REMINDER = "followup_reminder"

@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    company_name: str
    industry: str
    company_size: str
    location: str
    investment_capacity_usd: float
    technology_focus: List[str]
    registration_date: str
    contact_info: Dict[str, str]

@dataclass
class PolicyRecommendation:
    """政策推荐"""
    policy_id: str
    title: str
    location: str
    match_score: float
    estimated_benefits_usd: float
    key_requirements: List[str]
    application_deadline: Optional[str]
    priority: str  # high, medium, low
    reasoning: str

@dataclass
class ApplicationGuidance:
    """申请指导"""
    policy_id: str
    step_by_step_guide: List[Dict[str, Any]]
    required_documents: List[str]
    estimated_processing_time_days: int
    success_factors: List[str]
    common_pitfalls: List[str]
    contact_department: Dict[str, str]

@dataclass
class ComplianceCheck:
    """合规检查"""
    policy_id: str
    compliance_status: str  # compliant, non_compliant, partial_compliant
    compliance_score: float
    missing_requirements: List[str]
    recommendations: List[str]
    risk_level: str  # low, medium, high

@dataclass
class AgentResponse:
    """AI Agent响应"""
    action_type: AgentActionType
    success: bool
    message: str
    data: Any
    timestamp: str
    processing_time_ms: float

class PolicyAIAgent:
    """AI政策智能助手"""
    
    def __init__(self, db_path: str = "policy_database.db"):
        self.db_service = PolicyDatabaseService(db_path)
        self.cleaning_service = DataCleaningService(self.db_service)
        self.cleaner = PolicyCleaner()
        
        # 用户档案缓存
        self.user_profiles = {}
        
        # 会话历史
        self.session_history = {}
        
        logger.info("Policy AI Agent initialized successfully")
    
    def process_user_request(self, user_id: str, request: str, user_context: Dict[str, Any] = None) -> AgentResponse:
        """
        处理用户请求
        
        Args:
            user_id: 用户ID
            request: 用户请求文本
            user_context: 用户上下文信息
            
        Returns:
            AgentResponse: AI Agent响应
        """
        import time
        start_time = time.time()
        
        try:
            # 解析用户意图
            intent = self._parse_user_intent(request)
            
            # 获取或创建用户档案
            user_profile = self._get_or_create_user_profile(user_id, user_context)
            
            # 根据意图执行相应动作
            if intent == AgentActionType.POLICY_SEARCH:
                response = self._handle_policy_search(user_profile, request)
            elif intent == AgentActionType.POLICY_RECOMMENDATION:
                response = self._handle_policy_recommendation(user_profile)
            elif intent == AgentActionType.APPLICATION_GUIDANCE:
                response = self._handle_application_guidance(user_profile, request)
            elif intent == AgentActionType.COMPLIANCE_CHECK:
                response = self._handle_compliance_check(user_profile, request)
            elif intent == AgentActionType.ELIGIBILITY_ASSESSMENT:
                response = self._handle_eligibility_assessment(user_profile, request)
            elif intent == AgentActionType.BENEFIT_CALCULATION:
                response = self._handle_benefit_calculation(user_profile, request)
            else:
                response = AgentResponse(
                    action_type=intent,
                    success=False,
                    message="无法理解您的请求，请尝试重新描述",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 记录会话历史
            self._record_session(user_id, request, response)
            
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            return AgentResponse(
                action_type=AgentActionType.POLICY_SEARCH,
                success=False,
                message=f"处理请求时发生错误: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def _parse_user_intent(self, request: str) -> AgentActionType:
        """解析用户意图"""
        request_lower = request.lower()
        
        # 搜索相关关键词
        search_keywords = ["搜索", "查找", "找", "search", "find", "look for"]
        recommendation_keywords = ["推荐", "适合", "推荐", "recommend", "suitable", "match"]
        application_keywords = ["申请", "如何申请", "申请流程", "apply", "application", "how to apply"]
        compliance_keywords = ["合规", "检查", "是否符合", "compliance", "check", "eligible"]
        eligibility_keywords = ["资格", "条件", "是否符合条件", "eligibility", "qualification", "criteria"]
        benefit_keywords = ["收益", "补贴", "优惠", "benefit", "subsidy", "incentive", "how much"]
        
        # 检查意图
        if any(keyword in request_lower for keyword in search_keywords):
            return AgentActionType.POLICY_SEARCH
        elif any(keyword in request_lower for keyword in recommendation_keywords):
            return AgentActionType.POLICY_RECOMMENDATION
        elif any(keyword in request_lower for keyword in application_keywords):
            return AgentActionType.APPLICATION_GUIDANCE
        elif any(keyword in request_lower for keyword in compliance_keywords):
            return AgentActionType.COMPLIANCE_CHECK
        elif any(keyword in request_lower for keyword in eligibility_keywords):
            return AgentActionType.ELIGIBILITY_ASSESSMENT
        elif any(keyword in request_lower for keyword in benefit_keywords):
            return AgentActionType.BENEFIT_CALCULATION
        else:
            # 默认为搜索
            return AgentActionType.POLICY_SEARCH
    
    def _get_or_create_user_profile(self, user_id: str, context: Dict[str, Any] = None) -> UserProfile:
        """获取或创建用户档案"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        # 如果没有提供上下文，创建默认档案
        if not context:
            context = {
                "company_name": "Unknown Company",
                "industry": "other",
                "company_size": "small",
                "location": "Unknown",
                "investment_capacity_usd": 100000,
                "technology_focus": [],
                "registration_date": datetime.now().isoformat(),
                "contact_info": {}
            }
        
        user_profile = UserProfile(
            user_id=user_id,
            company_name=context.get("company_name", "Unknown Company"),
            industry=context.get("industry", "other"),
            company_size=context.get("company_size", "small"),
            location=context.get("location", "Unknown"),
            investment_capacity_usd=context.get("investment_capacity_usd", 100000),
            technology_focus=context.get("technology_focus", []),
            registration_date=context.get("registration_date", datetime.now().isoformat()),
            contact_info=context.get("contact_info", {})
        )
        
        self.user_profiles[user_id] = user_profile
        return user_profile
    
    def _handle_policy_search(self, user_profile: UserProfile, request: str) -> AgentResponse:
        """处理政策搜索"""
        try:
            # 从请求中提取搜索条件
            search_terms = self._extract_search_terms(request)
            
            # 构建查询过滤器
            filter = PolicyQueryFilter(
                keywords=search_terms,
                limit=20
            )
            
            # 执行搜索
            result = self.db_service.search_policies(filter)
            
            # 格式化搜索结果
            formatted_results = []
            for policy in result.policies:
                formatted_results.append({
                    "policy_id": policy.get("policy_id"),
                    "title": policy.get("title"),
                    "location": policy.get("location"),
                    "industry": policy.get("industry"),
                    "policy_type": policy.get("policy_type"),
                    "description": policy.get("description", "")[:200] + "...",
                    "match_score": self._calculate_search_score(policy, search_terms)
                })
            
            # 按匹配分数排序
            formatted_results.sort(key=lambda x: x["match_score"], reverse=True)
            
            return AgentResponse(
                action_type=AgentActionType.POLICY_SEARCH,
                success=True,
                message=f"找到 {len(formatted_results)} 个相关政策",
                data={
                    "search_results": formatted_results,
                    "total_count": result.total_count,
                    "search_terms": search_terms
                },
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Error in policy search: {e}")
            return AgentResponse(
                action_type=AgentActionType.POLICY_SEARCH,
                success=False,
                message=f"搜索失败: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def _handle_policy_recommendation(self, user_profile: UserProfile) -> AgentResponse:
        """处理政策推荐"""
        try:
            recommendations = []
            
            # 基于用户档案搜索相关政策
            filter = PolicyQueryFilter(
                country=self._map_country(user_profile.location),
                industry=user_profile.industry,
                limit=10
            )
            
            result = self.db_service.search_policies(filter)
            
            # 为每个政策计算推荐分数
            for policy in result.policies:
                recommendation = PolicyRecommendation(
                    policy_id=policy.get("policy_id"),
                    title=policy.get("title"),
                    location=policy.get("location"),
                    match_score=self._calculate_recommendation_score(policy, user_profile),
                    estimated_benefits_usd=self._estimate_benefits(policy, user_profile),
                    key_requirements=self._extract_key_requirements(policy),
                    application_deadline=self._extract_application_deadline(policy),
                    priority=self._determine_priority(policy, user_profile),
                    reasoning=self._generate_recommendation_reasoning(policy, user_profile)
                )
                recommendations.append(recommendation)
            
            # 按匹配分数排序
            recommendations.sort(key=lambda x: x.match_score, reverse=True)
            
            return AgentResponse(
                action_type=AgentActionType.POLICY_RECOMMENDATION,
                success=True,
                message=f"为您推荐 {len(recommendations)} 个相关政策",
                data={
                    "recommendations": [self._recommendation_to_dict(r) for r in recommendations[:5]],
                    "user_profile": {
                        "industry": user_profile.industry,
                        "location": user_profile.location,
                        "company_size": user_profile.company_size
                    }
                },
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Error in policy recommendation: {e}")
            return AgentResponse(
                action_type=AgentActionType.POLICY_RECOMMENDATION,
                success=False,
                message=f"推荐失败: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def _handle_application_guidance(self, user_profile: UserProfile, request: str) -> AgentResponse:
        """处理申请指导"""
        try:
            # 从请求中提取政策ID
            policy_id = self._extract_policy_id(request)
            
            if not policy_id:
                return AgentResponse(
                    action_type=AgentActionType.APPLICATION_GUIDANCE,
                    success=False,
                    message="请提供具体的政策ID或政策名称",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 获取政策详情
            policy = self.db_service.get_policy(policy_id)
            if not policy:
                return AgentResponse(
                    action_type=AgentActionType.APPLICATION_GUIDANCE,
                    success=False,
                    message="未找到相关政策",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 生成申请指导
            guidance = ApplicationGuidance(
                policy_id=policy_id,
                step_by_step_guide=self._generate_step_by_step_guide(policy),
                required_documents=self._extract_required_documents(policy),
                estimated_processing_time_days=self._estimate_processing_time(policy),
                success_factors=self._extract_success_factors(policy),
                common_pitfalls=self._extract_common_pitfalls(policy),
                contact_department=self._get_contact_department(policy)
            )
            
            return AgentResponse(
                action_type=AgentActionType.APPLICATION_GUIDANCE,
                success=True,
                message=f"为您生成政策 {policy.get('title')} 的申请指导",
                data=self._guidance_to_dict(guidance),
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Error in application guidance: {e}")
            return AgentResponse(
                action_type=AgentActionType.APPLICATION_GUIDANCE,
                success=False,
                message=f"申请指导生成失败: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def _handle_compliance_check(self, user_profile: UserProfile, request: str) -> AgentResponse:
        """处理合规检查"""
        try:
            # 从请求中提取政策ID
            policy_id = self._extract_policy_id(request)
            
            if not policy_id:
                return AgentResponse(
                    action_type=AgentActionType.COMPLIANCE_CHECK,
                    success=False,
                    message="请提供具体的政策ID或政策名称",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 获取政策详情
            policy = self.db_service.get_policy(policy_id)
            if not policy:
                return AgentResponse(
                    action_type=AgentActionType.COMPLIANCE_CHECK,
                    success=False,
                    message="未找到相关政策",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 执行合规检查
            compliance_check = ComplianceCheck(
                policy_id=policy_id,
                compliance_status=self._check_compliance_status(policy, user_profile),
                compliance_score=self._calculate_compliance_score(policy, user_profile),
                missing_requirements=self._identify_missing_requirements(policy, user_profile),
                recommendations=self._generate_compliance_recommendations(policy, user_profile),
                risk_level=self._assess_risk_level(policy, user_profile)
            )
            
            return AgentResponse(
                action_type=AgentActionType.COMPLIANCE_CHECK,
                success=True,
                message=f"完成对政策 {policy.get('title')} 的合规检查",
                data=self._compliance_to_dict(compliance_check),
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Error in compliance check: {e}")
            return AgentResponse(
                action_type=AgentActionType.COMPLIANCE_CHECK,
                success=False,
                message=f"合规检查失败: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def _handle_eligibility_assessment(self, user_profile: UserProfile, request: str) -> AgentResponse:
        """处理资格评估"""
        try:
            # 从请求中提取政策ID
            policy_id = self._extract_policy_id(request)
            
            if not policy_id:
                return AgentResponse(
                    action_type=AgentActionType.ELIGIBILITY_ASSESSMENT,
                    success=False,
                    message="请提供具体的政策ID或政策名称",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 获取政策详情
            policy = self.db_service.get_policy(policy_id)
            if not policy:
                return AgentResponse(
                    action_type=AgentActionType.ELIGIBILITY_ASSESSMENT,
                    success=False,
                    message="未找到相关政策",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 评估资格
            eligibility_score = self._calculate_eligibility_score(policy, user_profile)
            eligible = eligibility_score >= 0.7
            
            return AgentResponse(
                action_type=AgentActionType.ELIGIBILITY_ASSESSMENT,
                success=True,
                message=f"资格评估完成，您{'符合' if eligible else '不符合'}该政策要求",
                data={
                    "policy_id": policy_id,
                    "policy_title": policy.get("title"),
                    "eligibility_score": eligibility_score,
                    "is_eligible": eligible,
                    "strengths": self._identify_strengths(policy, user_profile),
                    "weaknesses": self._identify_weaknesses(policy, user_profile),
                    "improvement_suggestions": self._generate_improvement_suggestions(policy, user_profile)
                },
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Error in eligibility assessment: {e}")
            return AgentResponse(
                action_type=AgentActionType.ELIGIBILITY_ASSESSMENT,
                success=False,
                message=f"资格评估失败: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    def _handle_benefit_calculation(self, user_profile: UserProfile, request: str) -> AgentResponse:
        """处理收益计算"""
        try:
            # 从请求中提取政策ID
            policy_id = self._extract_policy_id(request)
            
            if not policy_id:
                return AgentResponse(
                    action_type=AgentActionType.BENEFIT_CALCULATION,
                    success=False,
                    message="请提供具体的政策ID或政策名称",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 获取政策详情
            policy = self.db_service.get_policy(policy_id)
            if not policy:
                return AgentResponse(
                    action_type=AgentActionType.BENEFIT_CALCULATION,
                    success=False,
                    message="未找到相关政策",
                    data=None,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=0
                )
            
            # 计算收益
            benefits = self._calculate_benefits(policy, user_profile)
            
            return AgentResponse(
                action_type=AgentActionType.BENEFIT_CALCULATION,
                success=True,
                message=f"完成政策 {policy.get('title')} 的收益计算",
                data={
                    "policy_id": policy_id,
                    "policy_title": policy.get("title"),
                    "estimated_benefits": benefits,
                    "roi_analysis": self._calculate_roi(benefits, user_profile),
                    "comparison_with_alternatives": self._compare_with_alternatives(policy, user_profile)
                },
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Error in benefit calculation: {e}")
            return AgentResponse(
                action_type=AgentActionType.BENEFIT_CALCULATION,
                success=False,
                message=f"收益计算失败: {str(e)}",
                data=None,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0
            )
    
    # 辅助方法
    def _extract_search_terms(self, request: str) -> List[str]:
        """提取搜索关键词"""
        # 简单的关键词提取
        import re
        words = re.findall(r'\b\w+\b', request.lower())
        # 过滤掉常见停用词
        stop_words = {'我', '要', '的', '是', '在', '有', '和', '与', '或', '但', '请', '帮', '查找', '搜索'}
        return [word for word in words if word not in stop_words and len(word) > 1]
    
    def _calculate_search_score(self, policy: Dict[str, Any], search_terms: List[str]) -> float:
        """计算搜索匹配分数"""
        score = 0.0
        text = f"{policy.get('title', '')} {policy.get('description', '')}".lower()
        
        for term in search_terms:
            if term in text:
                score += 1.0
        
        return score / len(search_terms) if search_terms else 0.0
    
    def _map_country(self, location: str) -> str:
        """映射国家代码"""
        country_mapping = {
            "中国": "CN", "上海": "CN", "北京": "CN", "深圳": "CN",
            "美国": "US", "硅谷": "US", "加州": "US",
            "欧盟": "EU", "德国": "DE", "法国": "FR", "英国": "GB"
        }
        return country_mapping.get(location, "CN")
    
    def _calculate_recommendation_score(self, policy: Dict[str, Any], user_profile: UserProfile) -> float:
        """计算推荐分数"""
        score = 0.0
        
        # 行业匹配
        if policy.get("industry") == user_profile.industry:
            score += 0.4
        
        # 地理位置匹配
        if user_profile.location in policy.get("location", ""):
            score += 0.3
        
        # 政策类型匹配
        if user_profile.company_size == "large" and policy.get("policy_type") == "subsidy":
            score += 0.2
        elif user_profile.company_size == "small" and policy.get("policy_type") == "grant":
            score += 0.2
        
        # 技术匹配
        if user_profile.technology_focus:
            for tech in user_profile.technology_focus:
                if tech in policy.get("description", ""):
                    score += 0.1
        
        return min(score, 1.0)
    
    def _estimate_benefits(self, policy: Dict[str, Any], user_profile: UserProfile) -> float:
        """估算收益"""
        # 简单的收益估算逻辑
        base_benefits = {
            "tax_break": user_profile.investment_capacity_usd * 0.15,
            "subsidy": user_profile.investment_capacity_usd * 0.3,
            "grant": user_profile.investment_capacity_usd * 0.5,
            "land_grant": user_profile.investment_capacity_usd * 0.2
        }
        
        policy_type = policy.get("policy_type", "other")
        return base_benefits.get(policy_type, user_profile.investment_capacity_usd * 0.1)
    
    def _extract_key_requirements(self, policy: Dict[str, Any]) -> List[str]:
        """提取关键要求"""
        requirements = []
        if policy.get("requirements"):
            for req in policy.get("requirements", []):
                if req.get("mandatory"):
                    requirements.append(req.get("title", ""))
        return requirements[:5]  # 返回前5个关键要求
    
    def _extract_application_deadline(self, policy: Dict[str, Any]) -> Optional[str]:
        """提取申请截止日期"""
        # 这里应该从政策元数据中提取
        return None
    
    def _determine_priority(self, policy: Dict[str, Any], user_profile: UserProfile) -> str:
        """确定优先级"""
        score = self._calculate_recommendation_score(policy, user_profile)
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation_reasoning(self, policy: Dict[str, Any], user_profile: UserProfile) -> str:
        """生成推荐理由"""
        reasons = []
        
        if policy.get("industry") == user_profile.industry:
            reasons.append("行业匹配度高")
        
        if user_profile.location in policy.get("location", ""):
            reasons.append("地理位置匹配")
        
        if policy.get("policy_type") in ["subsidy", "grant"]:
            reasons.append("提供资金支持")
        
        return "、".join(reasons) if reasons else "一般性政策匹配"
    
    def _recommendation_to_dict(self, recommendation: PolicyRecommendation) -> Dict[str, Any]:
        """将推荐转换为字典"""
        return {
            "policy_id": recommendation.policy_id,
            "title": recommendation.title,
            "location": recommendation.location,
            "match_score": recommendation.match_score,
            "estimated_benefits_usd": recommendation.estimated_benefits_usd,
            "key_requirements": recommendation.key_requirements,
            "application_deadline": recommendation.application_deadline,
            "priority": recommendation.priority,
            "reasoning": recommendation.reasoning
        }
    
    def _extract_policy_id(self, request: str) -> Optional[str]:
        """从请求中提取政策ID"""
        # 简单的政策ID提取
        import re
        patterns = [
            r'政策ID[：:]\s*([a-zA-Z0-9_]+)',
            r'ID[：:]\s*([a-zA-Z0-9_]+)',
            r'([a-zA-Z0-9_]{20,})'  # 长字符串可能是政策ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request)
            if match:
                return match.group(1)
        
        return None
    
    def _generate_step_by_step_guide(self, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成分步申请指南"""
        return [
            {
                "step": 1,
                "title": "准备申请材料",
                "description": "收集公司资质证明、项目计划书等相关材料",
                "duration_days": 7
            },
            {
                "step": 2,
                "title": "在线提交申请",
                "description": "通过政务服务平台提交电子申请",
                "duration_days": 3
            },
            {
                "step": 3,
                "title": "材料审核",
                "description": "相关部门对申请材料进行审核",
                "duration_days": 15
            },
            {
                "step": 4,
                "title": "现场考察",
                "description": "如有需要，安排现场考察",
                "duration_days": 5
            },
            {
                "step": 5,
                "title": "审批公示",
                "description": "审批结果进行公示",
                "duration_days": 10
            }
        ]
    
    def _extract_required_documents(self, policy: Dict[str, Any]) -> List[str]:
        """提取所需文档"""
        return [
            "公司营业执照",
            "法定代表人身份证",
            "公司章程",
            "项目可行性研究报告",
            "财务报表",
            "知识产权证明",
            "银行资信证明"
        ]
    
    def _estimate_processing_time(self, policy: Dict[str, Any]) -> int:
        """估算处理时间"""
        return 45  # 天
    
    def _extract_success_factors(self, policy: Dict[str, Any]) -> List[str]:
        """提取成功因素"""
        return [
            "项目技术先进性",
            "市场前景良好",
            "团队能力强",
            "财务状况健康",
            "符合政策导向"
        ]
    
    def _extract_common_pitfalls(self, policy: Dict[str, Any]) -> List[str]:
        """提取常见陷阱"""
        return [
            "材料准备不充分",
            "项目描述不清晰",
            "财务数据不准确",
            "错过申请截止日期",
            "不符合政策基本要求"
        ]
    
    def _get_contact_department(self, policy: Dict[str, Any]) -> Dict[str, str]:
        """获取联系部门"""
        return {
            "部门": "经济发展局",
            "电话": "021-12345678",
            "邮箱": "contact@example.com",
            "地址": "上海市浦东新区张江科学城"
        }
    
    def _guidance_to_dict(self, guidance: ApplicationGuidance) -> Dict[str, Any]:
        """将申请指导转换为字典"""
        return {
            "policy_id": guidance.policy_id,
            "step_by_step_guide": guidance.step_by_step_guide,
            "required_documents": guidance.required_documents,
            "estimated_processing_time_days": guidance.estimated_processing_time_days,
            "success_factors": guidance.success_factors,
            "common_pitfalls": guidance.common_pitfalls,
            "contact_department": guidance.contact_department
        }
    
    def _check_compliance_status(self, policy: Dict[str, Any], user_profile: UserProfile) -> str:
        """检查合规状态"""
        # 简化的合规检查
        if user_profile.industry == policy.get("industry"):
            return "compliant"
        else:
            return "partial_compliant"
    
    def _calculate_compliance_score(self, policy: Dict[str, Any], user_profile: UserProfile) -> float:
        """计算合规分数"""
        if user_profile.industry == policy.get("industry"):
            return 0.9
        else:
            return 0.6
    
    def _identify_missing_requirements(self, policy: Dict[str, Any], user_profile: UserProfile) -> List[str]:
        """识别缺失要求"""
        missing = []
        
        # 检查行业匹配
        if user_profile.industry != policy.get("industry"):
            missing.append("行业不匹配")
        
        # 检查投资规模
        if user_profile.investment_capacity_usd < 100000:
            missing.append("投资规模不足")
        
        return missing
    
    def _generate_compliance_recommendations(self, policy: Dict[str, Any], user_profile: UserProfile) -> List[str]:
        """生成合规建议"""
        recommendations = []
        
        if user_profile.industry != policy.get("industry"):
            recommendations.append("考虑调整业务方向以符合政策要求")
        
        if user_profile.investment_capacity_usd < 100000:
            recommendations.append("寻找合作伙伴或增加投资规模")
        
        return recommendations
    
    def _assess_risk_level(self, policy: Dict[str, Any], user_profile: UserProfile) -> str:
        """评估风险等级"""
        if user_profile.industry == policy.get("industry"):
            return "low"
        else:
            return "medium"
    
    def _compliance_to_dict(self, compliance: ComplianceCheck) -> Dict[str, Any]:
        """将合规检查转换为字典"""
        return {
            "policy_id": compliance.policy_id,
            "compliance_status": compliance.compliance_status,
            "compliance_score": compliance.compliance_score,
            "missing_requirements": compliance.missing_requirements,
            "recommendations": compliance.recommendations,
            "risk_level": compliance.risk_level
        }
    
    def _calculate_eligibility_score(self, policy: Dict[str, Any], user_profile: UserProfile) -> float:
        """计算资格分数"""
        score = 0.0
        
        # 行业匹配
        if user_profile.industry == policy.get("industry"):
            score += 0.4
        
        # 地理位置匹配
        if user_profile.location in policy.get("location", ""):
            score += 0.3
        
        # 公司规模匹配
        if user_profile.company_size == "large" and policy.get("policy_type") == "subsidy":
            score += 0.2
        
        # 投资能力
        if user_profile.investment_capacity_usd >= 100000:
            score += 0.1
        
        return score
    
    def _identify_strengths(self, policy: Dict[str, Any], user_profile: UserProfile) -> List[str]:
        """识别优势"""
        strengths = []
        
        if user_profile.industry == policy.get("industry"):
            strengths.append("行业匹配度高")
        
        if user_profile.location in policy.get("location", ""):
            strengths.append("地理位置优势")
        
        return strengths
    
    def _identify_weaknesses(self, policy: Dict[str, Any], user_profile: UserProfile) -> List[str]:
        """识别劣势"""
        weaknesses = []
        
        if user_profile.industry != policy.get("industry"):
            weaknesses.append("行业不匹配")
        
        if user_profile.investment_capacity_usd < 100000:
            weaknesses.append("投资规模不足")
        
        return weaknesses
    
    def _generate_improvement_suggestions(self, policy: Dict[str, Any], user_profile: UserProfile) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if user_profile.industry != policy.get("industry"):
            suggestions.append("考虑拓展相关业务领域")
        
        if user_profile.investment_capacity_usd < 100000:
            suggestions.append("寻找战略投资者或合作伙伴")
        
        return suggestions
    
    def _calculate_benefits(self, policy: Dict[str, Any], user_profile: UserProfile) -> Dict[str, float]:
        """计算收益"""
        policy_type = policy.get("policy_type", "other")
        
        if policy_type == "tax_break":
            tax_rate = 0.25  # 假设25%税率
            savings = user_profile.investment_capacity_usd * tax_rate
            return {
                "tax_savings_usd": savings,
                "net_benefit_usd": savings,
                "roi_percentage": (savings / user_profile.investment_capacity_usd) * 100
            }
        elif policy_type == "subsidy":
            subsidy_amount = user_profile.investment_capacity_usd * 0.3
            return {
                "subsidy_amount_usd": subsidy_amount,
                "net_benefit_usd": subsidy_amount,
                "roi_percentage": (subsidy_amount / user_profile.investment_capacity_usd) * 100
            }
        else:
            return {
                "estimated_benefit_usd": user_profile.investment_capacity_usd * 0.1,
                "roi_percentage": 10.0
            }
    
    def _calculate_roi(self, benefits: Dict[str, float], user_profile: UserProfile) -> Dict[str, Any]:
        """计算投资回报率"""
        return {
            "roi_percentage": benefits.get("roi_percentage", 0),
            "payback_period_months": 12 / (benefits.get("roi_percentage", 1) / 100),
            "net_present_value_usd": benefits.get("net_benefit_usd", 0) * 3  # 简化计算
        }
    
    def _compare_with_alternatives(self, policy: Dict[str, Any], user_profile: UserProfile) -> Dict[str, Any]:
        """与替代方案比较"""
        return {
            "this_policy_rank": 1,
            "alternative_policies": [],
            "advantages": ["政策支持力度大", "申请流程相对简单"],
            "disadvantages": ["竞争激烈", "要求较高"]
        }
    
    def _record_session(self, user_id: str, request: str, response: AgentResponse):
        """记录会话历史"""
        if user_id not in self.session_history:
            self.session_history[user_id] = []
        
        self.session_history[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "response": response.__dict__
        })
        
        # 保持最近100条记录
        if len(self.session_history[user_id]) > 100:
            self.session_history[user_id] = self.session_history[user_id][-100:]
    
    def get_user_session_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户会话历史"""
        return self.session_history.get(user_id, [])
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户档案"""
        return self.user_profiles.get(user_id)

# 使用示例
if __name__ == "__main__":
    # 创建AI Agent实例
    agent = PolicyAIAgent()
    
    # 模拟用户请求
    user_id = "user_001"
    user_context = {
        "company_name": "AI Tech Solutions",
        "industry": "ai",
        "company_size": "medium",
        "location": "上海",
        "investment_capacity_usd": 500000,
        "technology_focus": ["机器学习", "自然语言处理"],
        "registration_date": "2023-01-01",
        "contact_info": {
            "email": "contact@aitech.com",
            "phone": "13800138000"
        }
    }
    
    # 测试不同类型的请求
    test_requests = [
        "帮我搜索上海的人工智能政策",
        "推荐一些适合我们公司的政策",
        "如何申请上海市的人工智能扶持政策？",
        "检查我们是否符合政策要求",
        "计算我们能获得多少补贴"
    ]
    
    for request in test_requests:
        print(f"\n=== 用户请求: {request} ===")
        response = agent.process_user_request(user_id, request, user_context)
        print(f"响应: {response.message}")
        if response.data:
            print(f"数据: {json.dumps(response.data, indent=2, ensure_ascii=False)}")