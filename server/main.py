"""
Open Invest Protocol Server
高科技项目方服务端实现
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import sys
import os
from typing import Dict, Any

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema.types import (
    JsonRpcRequest, JsonRpcResponse, ProtocolError, 
    ValidationError, MethodNotFoundError, InternalError
)
from services.tech_readiness_service import TechReadinessService
from services.landing_requirements_service import LandingRequirementsService
from services.economic_compliance_service import EconomicComplianceService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Open Invest Protocol Server",
    description="高科技项目方服务端 - 实现与政府招商局的安全合规互联",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
tech_readiness_service = TechReadinessService()
landing_requirements_service = LandingRequirementsService()
economic_compliance_service = EconomicComplianceService()


@app.post("/rpc")
async def json_rpc_endpoint(request: Request):
    """
    JSON-RPC 2.0 端点
    统一处理所有协议请求
    """
    try:
        # 解析请求体
        request_data = await request.json()
        
        # 验证 JSON-RPC 请求格式
        json_rpc_request = JsonRpcRequest(**request_data)
        
        # 根据方法名调用相应的服务
        method = json_rpc_request.method
        params = json_rpc_request.params
        
        if method == "get_tech_readiness":
            result = await tech_readiness_service.get_tech_readiness(params)
        elif method == "get_landing_requirements":
            result = await landing_requirements_service.get_landing_requirements(params)
        elif method == "get_economic_and_compliance":
            result = await economic_compliance_service.get_economic_and_compliance(params)
        else:
            raise MethodNotFoundError(method)
        
        # 返回 JSON-RPC 响应
        response = JsonRpcResponse(
            jsonrpc="2.0",
            result=result,
            id=json_rpc_request.id
        )
        
        return response.dict()
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        response = JsonRpcResponse(
            jsonrpc="2.0",
            error={
                "code": e.code,
                "message": e.message,
                "data": e.data
            },
            id=request_data.get("id") if isinstance(request_data, dict) else None
        )
        return response.dict()
        
    except MethodNotFoundError as e:
        logger.error(f"Method not found: {e.message}")
        response = JsonRpcResponse(
            jsonrpc="2.0",
            error={
                "code": e.code,
                "message": e.message
            },
            id=request_data.get("id") if isinstance(request_data, dict) else None
        )
        return response.dict()
        
    except InternalError as e:
        logger.error(f"Internal error: {e.message}")
        response = JsonRpcResponse(
            jsonrpc="2.0",
            error={
                "code": e.code,
                "message": e.message,
                "data": e.data
            },
            id=request_data.get("id") if isinstance(request_data, dict) else None
        )
        return response.dict()
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        response = JsonRpcResponse(
            jsonrpc="2.0",
            error={
                "code": -32603,
                "message": "Internal error",
                "data": {"error": str(e)}
            },
            id=request_data.get("id") if isinstance(request_data, dict) else None
        )
        return response.dict()


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "open-invest-protocol-server"}


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "Open Invest Protocol Server",
        "version": "1.0.0",
        "description": "高科技项目方服务端 - 实现与政府招商局的安全合规互联",
        "endpoints": {
            "rpc": "/rpc - JSON-RPC 2.0 endpoint",
            "health": "/health - Health check"
        }
    }


if __name__ == "__main__":
    from config.config import config
    
    logger.info(f"Starting Open Invest Protocol Server on {config.host}:{config.port}")
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.log_level.lower()
    )