"""
政策爬虫引擎启动脚本
用于启动全球政府政策情报爬虫
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from policy_crawler.crawlers.policy_crawler_engine import PolicyCrawlerEngine
from policy_crawler.processors.data_structurer import PolicyDataStructurer
from policy_crawler.processers.intelligence_aggregator import GlobalPolicyAggregator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('policy_crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    logger.info("启动全球政府政策情报爬虫引擎...")
    
    # 创建爬虫引擎
    crawler_engine = PolicyCrawlerEngine()
    
    # 创建数据结构化服务
    data_structurer = PolicyDataStructurer()
    
    # 创建情报聚合器
    aggregator = GlobalPolicyAggregator()
    
    try:
        # 步骤1: 爬取政策数据
        logger.info("步骤1: 爬取全球政策数据...")
        crawl_results = await crawler_engine.crawl_all_policies()
        
        # 步骤2: 处理和结构化数据
        logger.info("步骤2: 处理和结构化政策数据...")
        from policy_crawler.data.raw_policies.sample_raw_policies import RAW_POLICIES
        processing_result = await data_structurer.process_raw_policies(RAW_POLICIES)
        
        # 步骤3: 聚合全球政策
        logger.info("步骤3: 聚合全球政策数据...")
        aggregation_result = await aggregator.aggregate_global_policies()
        
        # 步骤4: 生成报告
        logger.info("步骤4: 生成分析报告...")
        
        # 输出结果摘要
        print("\n" + "="*60)
        print("全球政府政策情报爬虫运行结果")
        print("="*60)
        print(f"总政策数量: {aggregation_result.total_policies}")
        print(f"覆盖地区: {', '.join(aggregation_result.by_region.keys())}")
        print(f"热门行业: {', '.join([k for k, v in sorted(aggregation_result.by_industry.items(), key=lambda x: x[1], reverse=True)[:3]])}")
        print(f"平均优先级: {aggregation_result.average_priority:.1f}")
        print("="*60)
        
        # 保存结果
        import json
        from datetime import datetime
        
        # 保存聚合结果
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "aggregation_result": {
                "total_policies": aggregation_result.total_policies,
                "by_region": aggregation_result.by_region,
                "by_industry": aggregation_result.by_industry,
                "average_priority": aggregation_result.average_priority,
                "top_incentives": aggregation_result.top_incentives[:5],
                "recent_updates": aggregation_result.recent_updates[:5]
            },
            "crawl_results": crawl_results,
            "processing_stats": processing_result["stats"]
        }
        
        output_path = "../data/crawler_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"爬虫结果已保存到: {output_path}")
        
        # 步骤5: 启动Web服务（可选）
        logger.info("步骤5: 启动Web服务...")
        await start_web_service(aggregator)
        
    except Exception as e:
        logger.error(f"爬虫运行失败: {e}")
        raise

async def start_web_service(aggregator):
    """启动Web服务"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        
        app = FastAPI(title="Global Policy Intelligence API", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "Global Policy Intelligence API", "version": "1.0.0"}
        
        @app.get("/policies")
        async def get_policies(query: str = "", region: str = "", limit: int = 50):
            """获取政策列表"""
            try:
                filters = {}
                if region:
                    filters["jurisdiction"] = region
                
                result = await aggregator.search_policies(query, filters, limit)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/policies/{policy_id}")
        async def get_policy(policy_id: str):
            """获取特定政策"""
            try:
                # 这里应该添加根据ID获取政策的逻辑
                # 暂时返回模拟数据
                return {"policy_id": policy_id, "message": "Policy details"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/recommendations")
        async def get_recommendations(industry: str = "", region: str = "", min_investment: float = 0):
            """获取政策推荐"""
            try:
                project_requirements = {
                    "industry": industry,
                    "region": region,
                    "min_investment": min_investment
                }
                
                recommendations = await aggregator.get_policy_recommendations(project_requirements)
                return {"recommendations": recommendations}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/trends")
        async def get_trends(days: int = 30):
            """获取政策趋势"""
            try:
                trends = await aggregator.get_policy_trends(days)
                return trends
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/statistics")
        async def get_statistics():
            """获取统计信息"""
            try:
                stats = aggregator.get_aggregation_statistics()
                return stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        import uvicorn
        logger.info("Web服务启动在 http://localhost:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
        
    except ImportError:
        logger.warning("FastAPI未安装，跳过Web服务启动")
    except Exception as e:
        logger.error(f"Web服务启动失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())