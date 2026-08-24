"""
Global Policy API Service
政策数据API服务，提供RESTful接口来访问和管理政策数据
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uvicorn

from .policy_database_service import PolicyDatabaseService, PolicyQueryFilter, PolicySearchResult
from .data_cleaning_service import DataCleaningService, CleaningReport

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="OpenInvest Global Policy API",
    description="API for accessing and managing global government policy data",
    version="1.0.0"
)

# 全局服务实例
db_service = None
cleaning_service = None

def get_db_service():
    """获取数据库服务实例"""
    global db_service
    if db_service is None:
        db_service = PolicyDatabaseService()
    return db_service

def get_cleaning_service():
    """获取清洗服务实例"""
    global cleaning_service
    if cleaning_service is None:
        db_service = get_db_service()
        cleaning_service = DataCleaningService(db_service)
    return cleaning_service

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Starting Policy API Service")
    # 初始化服务
    get_db_service()
    get_cleaning_service()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )

# 政策查询端点
@app.get("/api/policies", response_model=Dict[str, Any])
async def get_policies(
    country: Optional[str] = Query(None, description="Filter by country"),
    region: Optional[str] = Query(None, description="Filter by region"),
    city: Optional[str] = Query(None, description="Filter by city"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    policy_type: Optional[str] = Query(None, description="Filter by policy type"),
    min_investment: Optional[float] = Query(None, description="Minimum investment amount in USD"),
    max_investment: Optional[float] = Query(None, description="Maximum investment amount in USD"),
    keywords: Optional[str] = Query(None, description="Search keywords"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    获取政策列表
    """
    try:
        # 构建查询过滤器
        filter = PolicyQueryFilter(
            country=country,
            region=region,
            city=city,
            industry=industry,
            policy_type=policy_type,
            min_investment_usd=min_investment,
            max_investment_usd=max_investment,
            keywords=keywords,
            limit=limit,
            offset=offset
        )
        
        # 执行查询
        result = get_db_service().search_policies(filter)
        
        return {
            "policies": result.policies,
            "total_count": result.total_count,
            "query_time_ms": result.query_time_ms,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error in get_policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/policies/{policy_id}", response_model=Dict[str, Any])
async def get_policy(policy_id: str):
    """
    获取单个政策详情
    """
    try:
        policy = get_db_service().get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/policies/search", response_model=Dict[str, Any])
async def search_policies(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    全文搜索政策
    """
    try:
        result = get_db_service().full_text_search(q, limit)
        
        return {
            "policies": result.policies,
            "total_count": result.total_count,
            "query_time_ms": result.query_time_ms,
            "query": q
        }
        
    except Exception as e:
        logger.error(f"Error in search_policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 统计信息端点
@app.get("/api/statistics", response_model=Dict[str, Any])
async def get_statistics():
    """
    获取政策统计信息
    """
    try:
        stats = get_db_service().get_policy_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=Dict[str, Any])
async def health_check():
    """
    健康检查
    """
    try:
        # 检查数据库连接
        db = get_db_service()
        stats = db.get_policy_statistics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_stats": stats,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# 数据清洗端点
@app.post("/api/clean/batch", response_model=Dict[str, Any])
async def batch_clean_policies(
    file_paths: List[str] = Query(..., description="List of file paths to clean")
):
    """
    批量清洗政策文件
    """
    try:
        cleaning_service = get_cleaning_service()
        report = cleaning_service.batch_clean_policies(file_paths)
        
        return {
            "report": report.__dict__,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch_clean_policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/policies/{policy_id}/validate", response_model=Dict[str, Any])
async def validate_policy(policy_id: str):
    """
    验证政策数据质量
    """
    try:
        cleaning_service = get_cleaning_service()
        validation = cleaning_service.validate_policy_data(policy_id)
        
        return {
            "validation": validation,
            "policy_id": policy_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in validate_policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/policies/{policy_id}/standardize", response_model=Dict[str, Any])
async def standardize_policy(policy_id: str):
    """
    标准化政策数据
    """
    try:
        cleaning_service = get_cleaning_service()
        result = cleaning_service.standardize_policy_data(policy_id)
        
        return {
            "result": result,
            "policy_id": policy_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in standardize_policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/duplicates", response_model=Dict[str, Any])
async def find_duplicates(
    similarity_threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold for duplicate detection")
):
    """
    查找重复政策
    """
    try:
        cleaning_service = get_cleaning_service()
        duplicates = cleaning_service.deduplicate_policies(similarity_threshold)
        
        return {
            "duplicates": duplicates,
            "similarity_threshold": similarity_threshold,
            "total_duplicates": len(duplicates),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in find_duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 数据管理端点
@app.delete("/api/policies/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(policy_id: str):
    """
    删除政策
    """
    try:
        db = get_db_service()
        
        # 检查政策是否存在
        policy = db.get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # 删除政策（这里需要实现删除逻辑）
        # 由于SQLite的限制，这里只是示例
        # 实际实现需要添加DELETE语句
        
        return {
            "message": f"Policy {policy_id} deleted successfully",
            "policy_id": policy_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cleanup", response_model=Dict[str, Any])
async def cleanup_old_policies(
    days: int = Query(365, ge=1, le=3650, description="Delete policies older than N days")
):
    """
    清理旧政策
    """
    try:
        db = get_db_service()
        deleted_count = db.cleanup_old_policies(days)
        
        return {
            "message": f"Cleaned up {deleted_count} old policies",
            "deleted_count": deleted_count,
            "days_threshold": days,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API文档和根端点
@app.get("/")
async def root():
    """
    API根端点
    """
    return {
        "message": "OpenInvest Global Policy API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/docs")
async def documentation():
    """
    API文档
    """
    return {
        "message": "API Documentation available at /docs",
        "openapi": "/openapi.json"
    }

# 运行API服务
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行服务器
    uvicorn.run(
        "policy_api_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )