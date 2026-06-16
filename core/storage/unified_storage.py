"""
AI-TP OS - 统一存储层 (libai-storage Python SDK)
以底层系统为本体，为应用层提供统一存储 API
"""

import json
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config.settings import StorageConfig


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def put(self, key: str, data: Any, namespace: str = "default") -> bool:
        pass

    @abstractmethod
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        pass

    @abstractmethod
    def delete(self, key: str, namespace: str = "default") -> bool:
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "", namespace: str = "default") -> List[str]:
        pass

    @abstractmethod
    def close(self):
        pass


class SQLiteBackend(StorageBackend):
    """SQLite 存储后端"""

    def __init__(self, db_path: str = "/data/ai-tp.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS storage (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (namespace, key)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_storage_ns_key ON storage(namespace, key)
        """)
        conn.commit()
        conn.close()

    def put(self, key: str, data: Any, namespace: str = "default") -> bool:
        try:
            conn = self._get_conn()
            now = time.time()
            value = json.dumps(data, ensure_ascii=False)
            conn.execute(
                """INSERT INTO storage (namespace, key, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(namespace, key) DO UPDATE SET
                   value=excluded.value, updated_at=excluded.updated_at""",
                (namespace, key, value, now, now),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[SQLiteBackend] put error: {e}")
            return False

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT value FROM storage WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
            if row:
                return json.loads(row["value"])
            return None
        except Exception as e:
            print(f"[SQLiteBackend] get error: {e}")
            return None

    def delete(self, key: str, namespace: str = "default") -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM storage WHERE namespace = ? AND key = ?",
                (namespace, key),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[SQLiteBackend] delete error: {e}")
            return False

    def list_keys(self, prefix: str = "", namespace: str = "default") -> List[str]:
        try:
            conn = self._get_conn()
            if prefix:
                rows = conn.execute(
                    "SELECT key FROM storage WHERE namespace = ? AND key LIKE ?",
                    (namespace, f"{prefix}%"),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT key FROM storage WHERE namespace = ?",
                    (namespace,),
                ).fetchall()
            return [row["key"] for row in rows]
        except Exception as e:
            print(f"[SQLiteBackend] list_keys error: {e}")
            return []

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


class MemoryBackend(StorageBackend):
    """内存存储后端"""

    def __init__(self, max_size: int = 10000):
        self.data: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self._lock = threading.Lock()

    def put(self, key: str, data: Any, namespace: str = "default") -> bool:
        with self._lock:
            if namespace not in self.data:
                self.data[namespace] = {}
            if len(self.data[namespace]) >= self.max_size and key not in self.data[namespace]:
                # LRU: 移除最旧的
                oldest = min(self.data[namespace].items(), key=lambda x: x[1].get("_at", 0))
                del self.data[namespace][oldest[0]]
            self.data[namespace][key] = {"value": data, "_at": time.time()}
            return True

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        with self._lock:
            ns = self.data.get(namespace, {})
            item = ns.get(key)
            if item:
                item["_at"] = time.time()
                return item["value"]
            return None

    def delete(self, key: str, namespace: str = "default") -> bool:
        with self._lock:
            ns = self.data.get(namespace, {})
            if key in ns:
                del ns[key]
                return True
            return False

    def list_keys(self, prefix: str = "", namespace: str = "default") -> List[str]:
        with self._lock:
            ns = self.data.get(namespace, {})
            if prefix:
                return [k for k in ns.keys() if k.startswith(prefix)]
            return list(ns.keys())

    def close(self):
        self.data.clear()


class UnifiedStorage:
    """
    AI-TP OS 统一存储管理器
    为所有应用层 Agent 提供统一的存储接口
    """

    def __init__(self, config: StorageConfig):
        self.config = config
        self.backend = self._create_backend()
        self._namespaces = {ns["name"]: ns for ns in config.namespaces}

    def _create_backend(self) -> StorageBackend:
        backend_type = self.config.backend
        if backend_type == "sqlite":
            return SQLiteBackend(self.config.sqlite.get("db_path", "/data/ai-tp.db"))
        elif backend_type == "memory":
            return MemoryBackend(self.config.memory.get("max_size", 10000))
        elif backend_type == "redis":
            # TODO: 实现 Redis 后端
            print("[UnifiedStorage] Redis backend not implemented, fallback to SQLite")
            return SQLiteBackend()
        else:
            return MemoryBackend()

    def _get_namespace(self, name: str) -> str:
        """获取命名空间配置"""
        ns = self._namespaces.get(name, {})
        return ns.get("name", name)

    def put(self, key: str, data: Any, namespace: str = "default") -> bool:
        """存储数据"""
        return self.backend.put(key, data, namespace)

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """读取数据"""
        return self.backend.get(key, namespace)

    def delete(self, key: str, namespace: str = "default") -> bool:
        """删除数据"""
        return self.backend.delete(key, namespace)

    def list_keys(self, prefix: str = "", namespace: str = "default") -> List[str]:
        """列出键"""
        return self.backend.list_keys(prefix, namespace)

    # Agent 记忆专用接口
    def save_memory(self, agent_id: str, memory: Dict[str, Any]) -> bool:
        """保存 Agent 记忆"""
        key = f"memory:{agent_id}"
        return self.put(key, memory, namespace="agent_memory")

    def load_memory(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载 Agent 记忆"""
        key = f"memory:{agent_id}"
        return self.get(key, namespace="agent_memory")

    def save_conversation(self, session_id: str, messages: List[Dict]) -> bool:
        """保存对话历史"""
        key = f"conversation:{session_id}"
        return self.put(key, messages, namespace="agent_memory")

    def load_conversation(self, session_id: str) -> Optional[List[Dict]]:
        """加载对话历史"""
        key = f"conversation:{session_id}"
        return self.get(key, namespace="agent_memory")

    def save_document(self, doc_id: str, content: Any, metadata: Optional[Dict] = None) -> bool:
        """保存 RAG 文档"""
        data = {"content": content, "metadata": metadata or {}, "timestamp": time.time()}
        return self.put(doc_id, data, namespace="rag_documents")

    def load_document(self, doc_id: str) -> Optional[Dict]:
        """加载 RAG 文档"""
        return self.get(doc_id, namespace="rag_documents")

    def close(self):
        """关闭存储"""
        self.backend.close()
