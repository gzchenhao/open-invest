"""
数据存储服务
提供安全的数据存储和检索功能，确保数据不出域
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .data_protection import DataProtectionService, SensitivityLevel

logger = logging.getLogger(__name__)


@dataclass
class ProjectRecord:
    """项目记录"""
    project_id: str
    name: str
    industry: str
    scale: str
    description: str
    contact_info: Dict[str, str]
    created_at: str
    updated_at: str
    status: str
    metadata: Dict[str, Any]


class DataStorageService:
    """数据存储服务类"""
    
    def __init__(self, data_dir: str = "../../data"):
        """初始化数据存储服务"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据保护服务
        self.data_protection = DataProtectionService()
        
        # 数据文件路径
        self.projects_file = self.data_dir / "projects.json"
        self.audit_log_file = self.data_dir / "audit_log.json"
        
        # 初始化数据文件
        self._init_data_files()
        
        # 内存缓存（用于提高性能）
        self._projects_cache: Dict[str, ProjectRecord] = {}
        self._cache_loaded = False
    
    def _init_data_files(self):
        """初始化数据文件"""
        if not self.projects_file.exists():
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump({"projects": []}, f, ensure_ascii=False, indent=2)
        
        if not self.audit_log_file.exists():
            with open(self.audit_log_file, 'w', encoding='utf-8') as f:
                json.dump({"logs": []}, f, ensure_ascii=False, indent=2)
    
    def _load_cache(self):
        """加载数据到缓存"""
        if self._cache_loaded:
            return
        
        try:
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._projects_cache = {
                    project_id: ProjectRecord(**project_data)
                    for project_id, project_data in data.get("projects", {}).items()
                }
            
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._projects_cache)} projects to cache")
            
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
            self._projects_cache = {}
    
    def _save_to_disk(self):
        """保存数据到磁盘"""
        try:
            # 转换为可序列化的格式
            projects_data = {
                project_id: asdict(project_record)
                for project_id, project_record in self._projects_cache.items()
            }
            
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump({"projects": projects_data}, f, ensure_ascii=False, indent=2)
            
            logger.info("Data saved to disk")
            
        except Exception as e:
            logger.error(f"Error saving to disk: {str(e)}")
    
    def _add_audit_log(self, operation: str, client_type: str, project_id: str, success: bool = True):
        """添加审计日志"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "client_type": client_type,
                "project_id": project_id,
                "success": success
            }
            
            # 读取现有日志
            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["logs"].append(log_entry)
            
            # 只保留最近1000条日志
            if len(data["logs"]) > 1000:
                data["logs"] = data["logs"][-1000:]
            
            with open(self.audit_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error adding audit log: {str(e)}")
    
    def create_project(self, project_data: Dict[str, Any], client_type: str = "internal_client") -> ProjectRecord:
        """
        创建新项目
        
        Args:
            project_data: 项目数据
            client_type: 客户端类型
            
        Returns:
            ProjectRecord: 创建的项目记录
        """
        try:
            # 验证数据访问权限
            if not self.data_protection.validate_data_access(project_data, client_type):
                raise PermissionError("Access denied for creating project")
            
            # 生成项目ID
            project_id = project_data.get("project_id", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # 创建项目记录
            project_record = ProjectRecord(
                project_id=project_id,
                name=project_data.get("name", ""),
                industry=project_data.get("industry", ""),
                scale=project_data.get("scale", ""),
                description=project_data.get("description", ""),
                contact_info=project_data.get("contact_info", {}),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                status="active",
                metadata=project_data.get("metadata", {})
            )
            
            # 加载缓存
            self._load_cache()
            
            # 检查项目是否已存在
            if project_id in self._projects_cache:
                raise ValueError(f"Project '{project_id}' already exists")
            
            # 添加到缓存
            self._projects_cache[project_id] = project_record
            
            # 保存到磁盘
            self._save_to_disk()
            
            # 添加审计日志
            self._add_audit_log("create", client_type, project_id)
            
            logger.info(f"Created project: {project_id}")
            return project_record
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            self._add_audit_log("create", client_type, project_data.get("project_id", "unknown"), False)
            raise
    
    def get_project(self, project_id: str, client_type: str = "public_client") -> Optional[ProjectRecord]:
        """
        获取项目信息
        
        Args:
            project_id: 项目ID
            client_type: 客户端类型
            
        Returns:
            Optional[ProjectRecord]: 项目记录，如果不存在则返回None
        """
        try:
            # 加载缓存
            self._load_cache()
            
            # 获取项目
            project_record = self._projects_cache.get(project_id)
            
            if not project_record:
                logger.warning(f"Project '{project_id}' not found")
                return None
            
            # 应用数据脱敏
            project_dict = asdict(project_record)
            masked_dict = self.data_protection.mask_sensitive_data(project_dict, client_type)
            
            # 转换回ProjectRecord
            return ProjectRecord(**masked_dict)
            
        except Exception as e:
            logger.error(f"Error getting project: {str(e)}")
            self._add_audit_log("get", client_type, project_id, False)
            return None
    
    def update_project(self, project_id: str, update_data: Dict[str, Any], client_type: str = "internal_client") -> bool:
        """
        更新项目信息
        
        Args:
            project_id: 项目ID
            update_data: 更新数据
            client_type: 客户端类型
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 加载缓存
            self._load_cache()
            
            # 检查项目是否存在
            if project_id not in self._projects_cache:
                logger.warning(f"Project '{project_id}' not found")
                return False
            
            # 验证数据访问权限
            if not self.data_protection.validate_data_access(update_data, client_type):
                raise PermissionError("Access denied for updating project")
            
            # 更新项目记录
            project_record = self._projects_cache[project_id]
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(project_record, key):
                    setattr(project_record, key, value)
            
            # 更新时间戳
            project_record.updated_at = datetime.now().isoformat()
            
            # 保存到磁盘
            self._save_to_disk()
            
            # 添加审计日志
            self._add_audit_log("update", client_type, project_id)
            
            logger.info(f"Updated project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            self._add_audit_log("update", client_type, project_id, False)
            return False
    
    def delete_project(self, project_id: str, client_type: str = "internal_client") -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
            client_type: 客户端类型
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 加载缓存
            self._load_cache()
            
            # 检查项目是否存在
            if project_id not in self._projects_cache:
                logger.warning(f"Project '{project_id}' not found")
                return False
            
            # 删除项目
            del self._projects_cache[project_id]
            
            # 保存到磁盘
            self._save_to_disk()
            
            # 添加审计日志
            self._add_audit_log("delete", client_type, project_id)
            
            logger.info(f"Deleted project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            self._add_audit_log("delete", client_type, project_id, False)
            return False
    
    def list_projects(self, client_type: str = "public_client") -> List[Dict[str, Any]]:
        """
        列出项目
        
        Args:
            client_type: 客户端类型
            
        Returns:
            List[Dict[str, Any]]: 项目列表
        """
        try:
            # 加载缓存
            self._load_cache()
            
            projects = []
            for project_record in self._projects_cache.values():
                project_dict = asdict(project_record)
                masked_dict = self.data_protection.mask_sensitive_data(project_dict, client_type)
                projects.append(masked_dict)
            
            return projects
            
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return []
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取审计日志
        
        Args:
            limit: 日志数量限制
            
        Returns:
            List[Dict[str, Any]]: 审计日志列表
        """
        try:
            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data["logs"][-limit:]
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        try:
            # 加载缓存
            self._load_cache()
            
            return {
                "total_projects": len(self._projects_cache),
                "data_directory": str(self.data_dir),
                "projects_file_size": self.projects_file.stat().st_size if self.projects_file.exists() else 0,
                "audit_log_file_size": self.audit_log_file.stat().st_size if self.audit_log_file.exists() else 0,
                "cache_loaded": self._cache_loaded
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {}