"""
服务端配置管理
"""

import os
from typing import Dict, Any
from pydantic import BaseModel


class ServerConfig(BaseModel):
    """服务器配置类"""
    host: str = "localhost"
    port: int = 8000
    debug: bool = True
    data_dir: str = "../../data"
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    log_level: str = "INFO"
    cors_origins: list = ["*"]
    rate_limit: int = 100  # requests per minute
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """从环境变量加载配置"""
        return cls(
            host=os.getenv("OIP_HOST", "localhost"),
            port=int(os.getenv("OIP_PORT", "8000")),
            debug=os.getenv("OIP_DEBUG", "True").lower() == "true",
            data_dir=os.getenv("OIP_DATA_DIR", "../../data"),
            max_request_size=int(os.getenv("OIP_MAX_REQUEST_SIZE", "10485760")),
            log_level=os.getenv("OIP_LOG_LEVEL", "INFO"),
            cors_origins=os.getenv("OIP_CORS_ORIGINS", "*").split(","),
            rate_limit=int(os.getenv("OIP_RATE_LIMIT", "100"))
        )


# 全局配置实例
config = ServerConfig.from_env()