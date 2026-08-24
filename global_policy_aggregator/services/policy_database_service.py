"""
Global Policy Database Service
Mock 政策数据库服务，提供政策数据的存储、查询和管理功能
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict

from processors.policy_cleaner import PolicyCleaner, StructuredPolicy

logger = logging.getLogger(__name__)

@dataclass
class PolicyQueryFilter:
    """政策查询过滤器"""
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    policy_type: Optional[str] = None
    min_investment_usd: Optional[float] = None
    max_investment_usd: Optional[float] = None
    keywords: Optional[str] = None
    limit: int = 50
    offset: int = 0

@dataclass
class PolicySearchResult:
    """政策搜索结果"""
    policies: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float

class PolicyDatabaseService:
    """政策数据库服务"""
    
    def __init__(self, db_path: str = "policy_database.db"):
        self.db_path = db_path
        self.cleaner = PolicyCleaner()
        self._init_database()
        
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建政策表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS policies (
                        policy_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        location TEXT,
                        country TEXT,
                        region TEXT,
                        city TEXT,
                        industry TEXT,
                        policy_type TEXT,
                        description TEXT,
                        raw_content TEXT,
                        incentives_json TEXT,
                        requirements_json TEXT,
                        compliance_json TEXT,
                        metadata_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        crawl_timestamp TIMESTAMP,
                        confidence_score REAL DEFAULT 0.0,
                        data_quality TEXT DEFAULT 'raw'
                    )
                ''')
                
                # 创建全文搜索表
                cursor.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS policy_search 
                    USING fts5(title, description, location, industry, policy_type, content='policies')
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_policies_country ON policies(country)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_policies_industry ON policies(industry)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_policies_policy_type ON policies(policy_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_policies_created_at ON policies(created_at)')
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_policy(self, structured_policy: StructuredPolicy, source_url: str = None) -> str:
        """添加政策到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO policies (
                        policy_id, title, location, country, region, city, 
                        industry, policy_type, description, raw_content,
                        incentives_json, requirements_json, compliance_json, 
                        metadata_json, crawl_timestamp, confidence_score, data_quality
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    structured_policy.policy_id,
                    structured_policy.title,
                    structured_policy.location,
                    structured_policy.country,
                    structured_policy.region,
                    getattr(structured_policy, 'city', ''),
                    structured_policy.industry,
                    structured_policy.policy_type,
                    structured_policy.description,
                    json.dumps(structured_policy.metadata.get('raw_text', ''), ensure_ascii=False),
                    json.dumps(structured_policy.incentives, ensure_ascii=False),
                    json.dumps(structured_policy.requirements, ensure_ascii=False),
                    json.dumps(structured_policy.compliance_standards, ensure_ascii=False),
                    json.dumps(structured_policy.metadata, ensure_ascii=False),
                    structured_policy.metadata.get('crawl_timestamp'),
                    structured_policy.metadata.get('confidence_score', 0.0),
                    structured_policy.metadata.get('data_quality', 'raw')
                ))
                
                # 更新全文搜索索引
                cursor.execute('''
                    INSERT OR REPLACE INTO policy_search (
                        rowid, title, description, location, industry, policy_type
                    ) VALUES (
                        (SELECT rowid FROM policies WHERE policy_id = ?),
                        ?, ?, ?, ?, ?
                    )
                ''', (
                    structured_policy.policy_id,
                    structured_policy.title,
                    structured_policy.description,
                    structured_policy.location,
                    structured_policy.industry,
                    structured_policy.policy_type
                ))
                
                conn.commit()
                logger.info(f"Policy {structured_policy.policy_id} added to database")
                return structured_policy.policy_id
                
        except Exception as e:
            logger.error(f"Failed to add policy to database: {e}")
            raise
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """获取单个政策"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM policies WHERE policy_id = ?
                ''', (policy_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(cursor, row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get policy {policy_id}: {e}")
            return None
    
    def search_policies(self, filter: PolicyQueryFilter) -> PolicySearchResult:
        """搜索政策"""
        try:
            start_time = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                conditions = []
                params = []
                
                if filter.country:
                    conditions.append("country = ?")
                    params.append(filter.country)
                
                if filter.region:
                    conditions.append("region = ?")
                    params.append(filter.region)
                
                if filter.city:
                    conditions.append("city = ?")
                    params.append(filter.city)
                
                if filter.industry:
                    conditions.append("industry = ?")
                    params.append(filter.industry)
                
                if filter.policy_type:
                    conditions.append("policy_type = ?")
                    params.append(filter.policy_type)
                
                # 注：SQLite版本不支持JSON函数，暂时跳过投资金额过滤
                # if filter.min_investment_usd:
                #     conditions.append("JSON_EXTRACT(incentives_json, '$[0].amount_details.max_amount_usd') >= ?")
                #     params.append(filter.min_investment_usd)
                # 
                # if filter.max_investment_usd:
                #     conditions.append("JSON_EXTRACT(incentives_json, '$[0].amount_details.max_amount_usd') <= ?")
                #     params.append(filter.max_investment_usd)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # 获取总数
                count_query = f"SELECT COUNT(*) FROM policies WHERE {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # 获取政策列表
                query = f'''
                    SELECT * FROM policies 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                '''
                params.extend([filter.limit, filter.offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                policies = [self._row_to_dict(cursor, row) for row in rows]
                
                query_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return PolicySearchResult(
                    policies=policies,
                    total_count=total_count,
                    query_time_ms=query_time
                )
                
        except Exception as e:
            logger.error(f"Failed to search policies: {e}")
            return PolicySearchResult([], 0, 0)
    
    def full_text_search(self, query: str, limit: int = 50) -> PolicySearchResult:
        """全文搜索"""
        try:
            start_time = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 使用FTS5进行全文搜索
                cursor.execute('''
                    SELECT * FROM policies 
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', limit))
                
                rows = cursor.fetchall()
                policies = [self._row_to_dict(cursor, row) for row in rows]
                
                query_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return PolicySearchResult(
                    policies=policies,
                    total_count=len(policies),
                    query_time_ms=query_time
                )
                
        except Exception as e:
            logger.error(f"Failed to full text search: {e}")
            return PolicySearchResult([], 0, 0)
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """获取政策统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总政策数
                cursor.execute("SELECT COUNT(*) FROM policies")
                total_policies = cursor.fetchone()[0]
                
                # 按国家统计
                cursor.execute('''
                    SELECT country, COUNT(*) 
                    FROM policies 
                    GROUP BY country 
                    ORDER BY COUNT(*) DESC
                ''')
                country_stats = dict(cursor.fetchall())
                
                # 按行业统计
                cursor.execute('''
                    SELECT industry, COUNT(*) 
                    FROM policies 
                    GROUP BY industry 
                    ORDER BY COUNT(*) DESC
                ''')
                industry_stats = dict(cursor.fetchall())
                
                # 按政策类型统计
                cursor.execute('''
                    SELECT policy_type, COUNT(*) 
                    FROM policies 
                    GROUP BY policy_type 
                    ORDER BY COUNT(*) DESC
                ''')
                policy_type_stats = dict(cursor.fetchall())
                
                # 最近30天新增政策数
                cursor.execute('''
                    SELECT COUNT(*) FROM policies 
                    WHERE created_at >= datetime('now', '-30 days')
                ''')
                recent_policies = cursor.fetchone()[0]
                
                return {
                    "total_policies": total_policies,
                    "by_country": country_stats,
                    "by_industry": industry_stats,
                    "by_policy_type": policy_type_stats,
                    "recent_30_days": recent_policies,
                    "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get policy statistics: {e}")
            return {}
    
    def _row_to_dict(self, cursor, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, row))
        
        # 解析JSON字段
        if result.get('incentives_json'):
            try:
                result['incentives'] = json.loads(result['incentives_json'])
            except:
                result['incentives'] = []
        
        if result.get('requirements_json'):
            try:
                result['requirements'] = json.loads(result['requirements_json'])
            except:
                result['requirements'] = []
        
        if result.get('compliance_json'):
            try:
                result['compliance_standards'] = json.loads(result['compliance_json'])
            except:
                result['compliance_standards'] = []
        
        if result.get('metadata_json'):
            try:
                result['metadata'] = json.loads(result['metadata_json'])
            except:
                result['metadata'] = {}
        
        return result
    
    def cleanup_old_policies(self, days: int = 365):
        """清理旧政策"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM policies 
                    WHERE created_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old policies")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old policies: {e}")
            return 0

# 使用示例
if __name__ == "__main__":
    # 创建数据库服务实例
    db_service = PolicyDatabaseService()
    
    # 示例政策数据
    sample_policy_text = """
    《上海市张江科学城人工智能产业扶持政策（2024年）》
    
    为促进人工智能产业发展，特制定本政策。对在张江科学城注册的人工智能企业，给予以下支持：
    
    1. 税收优惠：企业所得税减免50%，最高不超过500万元；增值税即征即退政策。
    2. 财政补贴：研发费用补贴30%，最高1000万元；办公场地租金补贴50%，最高200万元/年。
    3. 人员要求：研发人员不少于20人，博士占比不低于30%。
    4. 知识产权：拥有发明专利不少于5项，软件著作权不少于10项。
    5. 投资要求：固定资产投资不低于2000万元人民币。
    6. 数据本地化：用户数据必须存储在境内服务器。
    7. 出口管制：涉及核心技术的出口需要审批。
    
    本政策自2024年1月1日起实施，有效期至2026年12月31日。
    """
    
    # 创建清洗器并清洗政策
    cleaner = PolicyCleaner()
    structured_policy = cleaner.clean_policy_text(sample_policy_text, "http://example.com/policy")
    
    # 添加到数据库
    policy_id = db_service.add_policy(structured_policy)
    print(f"Policy added with ID: {policy_id}")
    
    # 搜索政策
    filter = PolicyQueryFilter(
        country="中国",
        industry="ai",
        limit=10
    )
    result = db_service.search_policies(filter)
    print(f"Found {result.total_count} policies")
    
    # 全文搜索
    search_result = db_service.full_text_search("人工智能")
    print(f"Full text search found {search_result.total_count} policies")
    
    # 获取统计信息
    stats = db_service.get_policy_statistics()
    print(f"Database statistics: {stats}")