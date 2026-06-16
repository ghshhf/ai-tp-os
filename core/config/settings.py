"""
AI-TP OS - 统一配置管理
以底层系统为本体，整合应用层配置
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InferenceBackend(BaseSettings):
    """推理后端配置"""
    enabled: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = ""
    timeout: int = 120


class InferenceConfig(BaseSettings):
    """推理层配置 (计算层)"""
    default_backend: str = "ollama"
    backends: Dict[str, InferenceBackend] = Field(default_factory=dict)
    fallback: Dict[str, Any] = Field(default_factory=dict)


class StorageConfig(BaseSettings):
    """存储层配置 (libai-storage)"""
    backend: str = "sqlite"
    shared: bool = True
    sqlite: Dict[str, Any] = Field(default_factory=lambda: {"db_path": "/data/ai-tp.db"})
    redis: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=lambda: {"max_size": 10000})
    namespaces: List[Dict[str, Any]] = Field(default_factory=list)


class NetworkConfig(BaseSettings):
    """网络层配置 (ai-tp-discovery)"""
    enabled: bool = True
    mode: str = "hybrid"
    discovery: Dict[str, Any] = Field(default_factory=dict)
    gateway: Dict[str, Any] = Field(default_factory=dict)
    p2p: Dict[str, Any] = Field(default_factory=dict)
    nat: Dict[str, Any] = Field(default_factory=dict)


class SchedulerConfig(BaseSettings):
    """计算层配置 (ai-tp-scheduler)"""
    enabled: bool = False
    backend: str = "local"
    local: Dict[str, Any] = Field(default_factory=dict)
    distributed: Dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseSettings):
    """安全配置"""
    encryption: Dict[str, Any] = Field(default_factory=dict)
    privacy: Dict[str, Any] = Field(default_factory=dict)


class MonitoringConfig(BaseSettings):
    """监控配置"""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30


class AITPOSConfig(BaseSettings):
    """
    AI-TP OS 统一配置
    整合底层系统 (glibc-packages) 和应用层 (awesome-llm-apps)
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # 系统模式
    mode: str = "standalone"

    # 日志
    logging: Dict[str, Any] = Field(default_factory=dict)

    # 三层架构配置
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

    # 应用层
    apps: Dict[str, Any] = Field(default_factory=dict)

    # 安全
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # 监控
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    @classmethod
    def from_yaml(cls, path: str = "ai-tp-config.yaml") -> "AITPOSConfig":
        """从 YAML 文件加载配置"""
        config_path = Path(path)
        if not config_path.exists():
            # 尝试从工作目录查找
            config_path = Path("/ai-tp-os") / path
            if not config_path.exists():
                return cls()

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def get_inference_client(self, backend: Optional[str] = None):
        """
        获取推理客户端
        优先本地 (ollama)，其次云 API
        """
        backend_name = backend or self.inference.default_backend
        backend_config = self.inference.backends.get(backend_name)

        if not backend_config or not backend_config.enabled:
            # 尝试 fallback
            if self.inference.fallback.get("enabled"):
                for fb in self.inference.fallback.get("order", []):
                    fb_config = self.inference.backends.get(fb)
                    if fb_config and fb_config.enabled:
                        return self._create_client(fb, fb_config)
            raise RuntimeError(f"No available inference backend: {backend_name}")

        return self._create_client(backend_name, backend_config)

    def _create_client(self, name: str, config: InferenceBackend):
        """创建推理客户端"""
        if name == "ollama":
            from core.compute.ollama_client import OllamaClient
            return OllamaClient(host=config.base_url or "http://localhost:11434")
        elif name == "openai":
            from openai import OpenAI
            return OpenAI(api_key=config.api_key, base_url=config.base_url)
        elif name == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=config.api_key)
        elif name == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            return genai
        else:
            raise ValueError(f"Unknown backend: {name}")

    def get_storage(self):
        """获取存储实例"""
        from core.storage.unified_storage import UnifiedStorage
        return UnifiedStorage(self.storage)

    def get_network_manager(self):
        """获取网络管理器"""
        from core.network.manager import NetworkManager
        return NetworkManager(self.network)


# 全局配置实例
_config: Optional[AITPOSConfig] = None


def get_config() -> AITPOSConfig:
    """获取全局配置（单例）"""
    global _config
    if _config is None:
        _config = AITPOSConfig.from_yaml()
    return _config


def reload_config() -> AITPOSConfig:
    """重新加载配置"""
    global _config
    _config = AITPOSConfig.from_yaml()
    return _config
