"""
AI Agent Web Interface
AI智能助手Web界面，提供用户友好的交互界面
"""

from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime

import sys
sys.path.append('..')
from agents.policy_ai_agent import PolicyAIAgent, UserProfile, AgentResponse
from services.policy_database_service import PolicyDatabaseService

# 创建FastAPI应用
app = FastAPI(
    title="OpenInvest AI Policy Agent",
    description="AI智能政策助手Web界面",
    version="1.0.0"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建AI Agent实例，使用正确的数据库路径
agent = PolicyAIAgent(db_path="../data/seed_data/policy_database.db")

# 模板配置
templates = Jinja2Templates(directory="../global_policy_aggregator/web/templates")

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 用户会话存储
user_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """聊天界面"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """测试页面"""
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/simple", response_class=HTMLResponse)
async def simple_page(request: Request):
    """简单测试页面"""
    return HTMLResponse('<h1>简单测试页面</h1><p>不使用模板的测试</p>')

@app.get("/english", response_class=HTMLResponse)
async def english_page(request: Request):
    """英文测试页面"""
    import os
    absolute_path = os.path.abspath('../global_policy_aggregator/web/templates/english.html')
    with open(absolute_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HTMLResponse(content)

@app.post("/api/chat")
async def chat_message(
    request: Request,
    message: str = Form(...),
    user_id: str = Form("default_user"),
    user_context: str = Form("{}")
):
    """处理聊天消息"""
    try:
        # 解析用户上下文
        context = json.loads(user_context)
        
        # 处理用户消息
        response = agent.process_user_request(user_id, message, context)
        
        # 存储会话
        if user_id not in user_sessions:
            user_sessions[user_id] = []
        
        user_sessions[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "ai_response": response.__dict__
        })
        
        return JSONResponse(content={
            "success": True,
            "response": response.message,
            "data": response.data,
            "action_type": response.action_type.value,
            "processing_time_ms": response.processing_time_ms
        })
        
    except Exception as e:
        logger.error(f"Error in chat message: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """获取用户档案"""
    try:
        profile = agent.get_user_profile(user_id)
        if profile:
            return JSONResponse(content={
                "success": True,
                "profile": {
                    "user_id": profile.user_id,
                    "company_name": profile.company_name,
                    "industry": profile.industry,
                    "company_size": profile.company_size,
                    "location": profile.location,
                    "investment_capacity_usd": profile.investment_capacity_usd,
                    "technology_focus": profile.technology_focus,
                    "registration_date": profile.registration_date
                }
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "User profile not found"
            }, status_code=404)
            
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/user/{user_id}/profile")
async def update_user_profile(
    user_id: str,
    company_name: str = Form(...),
    industry: str = Form(...),
    company_size: str = Form(...),
    location: str = Form(...),
    investment_capacity_usd: float = Form(...),
    technology_focus: str = Form("[]"),
    contact_email: str = Form(""),
    contact_phone: str = Form("")
):
    """更新用户档案"""
    try:
        # 解析技术焦点
        tech_focus = json.loads(technology_focus)
        
        # 构建用户上下文
        context = {
            "company_name": company_name,
            "industry": industry,
            "company_size": company_size,
            "location": location,
            "investment_capacity_usd": investment_capacity_usd,
            "technology_focus": tech_focus,
            "registration_date": datetime.now().isoformat(),
            "contact_info": {
                "email": contact_email,
                "phone": contact_phone
            }
        }
        
        # 创建用户档案
        agent._get_or_create_user_profile(user_id, context)
        
        return JSONResponse(content={
            "success": True,
            "message": "User profile updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/user/{user_id}/history")
async def get_chat_history(user_id: str):
    """获取聊天历史"""
    try:
        history = agent.get_user_session_history(user_id)
        return JSONResponse(content={
            "success": True,
            "history": history
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/statistics")
async def get_statistics():
    """获取系统统计信息"""
    try:
        # 获取数据库统计
        db_stats = agent.db_service.get_policy_statistics()
        
        # 获取用户统计
        total_users = len(agent.user_profiles)
        active_sessions = len(user_sessions)
        
        return JSONResponse(content={
            "success": True,
            "statistics": {
                "database_stats": db_stats,
                "total_users": total_users,
                "active_sessions": active_sessions,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# API文档
@app.get("/docs")
async def documentation():
    """API文档"""
    return {
        "message": "API Documentation available at /docs",
        "openapi": "/openapi.json"
    }

# 运行Web服务器
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "ai_agent_interface:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )