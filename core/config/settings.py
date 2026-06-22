"""
AI-TP OS - 统一配置管理
以底层系统为本体，整合应用层配置

轻量化实现：纯 Python dataclass，不依赖 pydantic-settings。
支持 YAML（可选）和 JSON 配置文件，优先 JSON 兜底。
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# YAML 可选导入
try:
    import yaml

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# dotenv 可选导入
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class InferenceBackend:
    """推理后端配置"""
    enabled: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = ""
    timeout: int = 120


@dataclass
class InferenceConfig:
    """推理层配置 (计算层)"""
    default_backend: str = "ollama"
    backends: Dict[str, Any] = field(default_factory=dict)
    fallback: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageConfig:
    """存储层配置 (libai-storage)"""
    backend: str = "sqlite"
    shared: bool = True
    sqlite: Dict[str, Any] = field(default_factory=lambda: {"db_path": "data/ai-tp.db"})
    redis: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=lambda: {"max_size": 10000})
    namespaces: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NetworkConfig:
    """网络层配置 (ai-tp-discovery)"""
    enabled: bool = True
    mode: str = "hybrid"
    discovery: Dict[str, Any] = field(default_factory=dict)
    gateway: Dict[str, Any] = field(default_factory=dict)
    p2p: Dict[str, Any] = field(default_factory=dict)
    nat: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    """计算层配置 (ai-tp-scheduler)"""
    enabled: bool = False
    backend: str = "local"
    local: Dict[str, Any] = field(default_factory=dict)
    distributed: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """安全配置"""
    encryption: Dict[str, Any] = field(default_factory=dict)
    privacy: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30


@dataclass
class AITPOSConfig:
    """
    AI-TP OS 统一配置
    整合底层系统和应用层
    """

    # 系统模式
    mode: str = "standalone"

    # 日志
    logging: Dict[str, Any] = field(default_factory=dict)

    # 三层架构配置
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)

    # 应用层
    apps: Dict[str, Any] = field(default_factory=dict)

    # 安全
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # 监控
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    from_yaml(cls, path: str = "ai-tp-config.yaml") -> "AITPOSConfig":
        """从 YAML/JSON 配置文件加载"""
        config_path = Path(path)
        if not config_path.exists():
            # 尝试从工作目录查找
            config_path = Path.cwd() / path
            if not config_path.exists():
                # 尝试 JSON 兜底
                json_path = path.replace(".yaml", ".json").replace(".yml", ".json")
                config_path = Path(json_path)
                if not config_path.exists():
                    return cls()

        data = _load_config_file(config_path)
        if not data:
            return cls()

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "AITPOSConfig":
        """从字典创建配置（递归处理嵌套对象）"""
        # 处理环境变量覆盖
        data = _apply_env_overrides(data)

        cfg = cls()

        if "mode" in data:
            cfg.mode = data["mode"]
        if "logging" in data:
            cfg.logging = data["logging"]

        if "inference" in data:
            inf = data["inference"]
            if isinstance(inf, dict):
                cfg.inference = InferenceConfig(
                    default_backend=inf.get("default_backend", cfg.inference.default_backend),
                    backends=_build_sub_configs(InferenceBackend, inf.get("backends", {})),
                    fallback=inf.get("fallback", {}),
                )

        if "storage" in data:
            sto = data["storage"]
            if isinstance(sto, dict):
                cfg.storage = StorageConfig(
                    backend=sto.get("backend", cfg.storage.backend),
                    shared=sto.get("shared", cfg.storage.shared),
                    sqlite=sto.get("sqlite", cfg.storage.sqlite),
                    redis=sto.get("redis", cfg.storage.redis),
                    memory=sto.get("memory", cfg.storage.memory),
                    namespaces=sto.get("namespaces", cfg.storage.namespaces),
                )

        if "network" in data:
            net = data["network"]
            if isinstance(net, dict):
                cfg.network = NetworkConfig(
                    enabled=net.get("enabled", cfg.network.enabled),
                    mode=net.get("mode", cfg.network.mode),
                    discovery=net.get("discovery", cfg.network.discovery),
                    gateway=net.get("gateway", cfg.network.gateway),
                    p2p=net.get("p2p", cfg.network.p2p),
                    nat=net.get("nat", cfg.network.nat),
                )

        if "scheduler" in data:
            sch = data["scheduler"]
            if isinstance(sch, dict):
                cfg.scheduler = SchedulerConfig(
                    enabled=sch.get("enabled", cfg.scheduler.enabled),
                    backend=sch.get("backend", cfg.scheduler.backend),
                    local=sch.get("local", cfg.scheduler.local),
                    distributed=sch.get("distributed", cfg.scheduler.distributed),
                )

        if "apps" in data:
            cfg.apps = data["apps"]
        if "security" in data:
            sec = data["security"]
            if isinstance(sec, dict):
                cfg.security = SecurityConfig(
                    encryption=sec.get("encryption", {}),
                    privacy=sec.get("privacy", {}),
                )
        if "monitoring" in data:
            mon = data["monitoring"]
            if isinstance(mon, dict):
                cfg.monitoring = MonitoringConfig(
                    enabled=mon.get("enabled", cfg.monitoring.enabled),
                    metrics_port=mon.get("metrics_port", cfg.monitoring.metrics_port),
                    health_check_interval=mon.get("health_check_interval", cfg.monitoring.health_check_interval),
                )

        return cfg

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


# ──────────────────────────────────────
# 内部辅助函数
# ──────────────────────────────────────

def _load_config_file(path: Path) -> Optional[Dict[str, Any]]:
    """根据文件扩展名加载配置"""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if suffix in (".yaml", ".yml"):
        if _HAS_YAML:
            return yaml.safe_load(text)
        else:
            print(f"[settings] WARNING: PyYAML not installed, cannot parse {path}")
            return None
    elif suffix == ".json":
        return json.loads(text)
    else:
        print(f"[settings] WARNING: Unknown config format: {suffix}")
        return None


def _apply_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    """用环境变量覆盖配置（仅顶层简单字段）"""
    env_map = {
        "AI_TP_MODE": "mode",
        "AI_TP_STORAGE_BACKEND": ("storage", "backend"),
        "AI_TP_NETWORK_ENABLED": ("network", "enabled"),
        "AI_TP_NETWORK_MODE": ("network", "mode"),
    }
    for env_key, path_parts in env_map.items():
        value = os.environ.get(env_key)
        if value is None:
            continue
        if isinstance(path_parts, str):
            data[path_parts] = value
        elif isinstance(path_parts, tuple) and len(path_parts) == 2:
            section, key = path_parts
            if section not in data:
                data[section] = {}
            data[section][key] = _parse_bool(value) if key in ("enabled", "shared") else value
    return data


def _parse_bool(value: str) -> bool:
    """解析布尔字符串"""
    return value.lower() in ("true", "1", "yes", "on")


def _build_sub_configs(cls, data: Dict[str, Any]) -> Dict[str, Any]:
    """将字典值构建为 dataclass 实例"""
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            # 过滤掉 dataclass 不认识的字段
            valid = {k: v for k, v in value.items() if k in cls.__dataclass_fields__}
            result[key] = cls(**valid)
        else:
            result[key] = value
    return result


# ──────────────────────────────────────
# 兼容旧代码的别名
# ──────────────────────────────────────

def load_config(path: str = "ai-tp-config.yaml") -> Dict[str, Any]:
    """
    加载配置并返回字典（兼容 scripts/cli.py 的调用方式）
    """
    # 优先尝试 YAML
    config_path = Path(path)
    if config_path.exists():
        data = _load_config_file(config_path)
        if data:
            return _apply_env_overrides(data)

    # 尝试 JSON 兜底
    json_path = str(path).replace(".yaml", ".json").replace(".yml", ".json")
    config_path = Path(json_path)
    if config_path.exists():
        data = _load_config_file(config_path)
        if data:
            return _apply_env_overrides(data)

    return {
        "compute": {
            "backend": "ollama",
            "ollama_host": os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            "default_model": os.environ.get("OLLAMA_MODEL", "llama3.2"),
            "timeout": 120,
        },
        "storage": {
            "backend": os.environ.get("AI_TP_STORAGE_BACKEND", "sqlite"),
            "sqlite": {"db_path": "data/ai-tp.db"},
        },
        "network": {
            "enabled": os.environ.get("AI_TP_NETWORK_ENABLED", "false").lower() in ("true", "1"),
            "mode": os.environ.get("AI_TP_NETWORK_MODE", "local"),
        },
    }


# ──────────────────────────────────────
# 全局配置实例
# ──────────────────────────────────────

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
