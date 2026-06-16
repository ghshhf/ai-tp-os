"""
AI-TP OS - 网络管理器 (ai-tp-discovery Python SDK)
以底层系统为本体，为应用层提供 P2P 通信和节点发现能力
"""

import json
import socket
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from core.config.settings import NetworkConfig


class NetworkManager:
    """
    AI-TP OS 网络管理器
    提供节点发现、P2P 通信、NAT 穿透等网络能力
    """

    def __init__(self, config: NetworkConfig):
        self.config = config
        self.enabled = config.enabled
        self.mode = config.mode
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._listeners: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self):
        """启动网络服务"""
        if not self.enabled:
            print("[NetworkManager] Network is disabled")
            return

        self._running = True

        if self.mode in ("local", "hybrid"):
            self._start_local_discovery()

        if self.mode in ("mdns", "hybrid"):
            self._start_mdns_discovery()

        print(f"[NetworkManager] Started in {self.mode} mode")

    def stop(self):
        """停止网络服务"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print("[NetworkManager] Stopped")

    def _start_local_discovery(self):
        """启动本地发现（基于 UDP 广播）"""
        self._thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self._thread.start()

    def _discovery_loop(self):
        """发现循环"""
        port = self.config.discovery.get("port", 8472)
        interval = self.config.discovery.get("interval", 30)

        # 创建 UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", port))
        sock.settimeout(2)

        while self._running:
            try:
                # 发送心跳
                heartbeat = json.dumps({
                    "type": "heartbeat",
                    "node_id": self._get_node_id(),
                    "timestamp": time.time(),
                    "services": ["agent", "storage", "compute"],
                })
                sock.sendto(heartbeat.encode(), ("<broadcast>", port))

                # 接收响应
                try:
                    data, addr = sock.recvfrom(1024)
                    self._handle_discovery_message(data, addr)
                except socket.timeout:
                    pass

                time.sleep(interval)
            except Exception as e:
                print(f"[NetworkManager] Discovery error: {e}")
                time.sleep(5)

        sock.close()

    def _start_mdns_discovery(self):
        """启动 mDNS 发现（局域网）"""
        # TODO: 实现 mDNS 发现
        pass

    def _handle_discovery_message(self, data: bytes, addr: tuple):
        """处理发现消息"""
        try:
            msg = json.loads(data.decode())
            node_id = msg.get("node_id")
            if node_id and node_id != self._get_node_id():
                with self._lock:
                    self.nodes[node_id] = {
                        "address": addr[0],
                        "port": addr[1],
                        "last_seen": time.time(),
                        "services": msg.get("services", []),
                    }
                self._notify_listeners("node_discovered", node_id)
        except json.JSONDecodeError:
            pass

    def _get_node_id(self) -> str:
        """获取当前节点 ID"""
        # 基于主机名生成节点 ID
        return f"node-{socket.gethostname()}"

    def _notify_listeners(self, event: str, data: Any):
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(event, data)
            except Exception as e:
                print(f"[NetworkManager] Listener error: {e}")

    def add_listener(self, callback: Callable):
        """添加事件监听器"""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        """移除事件监听器"""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_nodes(self, service: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取发现的节点列表
        可按服务类型过滤
        """
        with self._lock:
            nodes = list(self.nodes.values())
            if service:
                nodes = [n for n in nodes if service in n.get("services", [])]
            return nodes

    def send_to_node(self, node_id: str, message: Dict[str, Any]) -> bool:
        """向指定节点发送消息"""
        with self._lock:
            node = self.nodes.get(node_id)
            if not node:
                return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((node["address"], node.get("port", 8473)))
            sock.send(json.dumps(message).encode())
            sock.close()
            return True
        except Exception as e:
            print(f"[NetworkManager] Send error: {e}")
            return False

    def broadcast(self, message: Dict[str, Any]):
        """广播消息到所有节点"""
        with self._lock:
            node_ids = list(self.nodes.keys())

        for node_id in node_ids:
            self.send_to_node(node_id, message)

    # Agent 间通信专用接口
    def send_agent_message(
        self,
        target_agent: str,
        message: str,
        sender: Optional[str] = None,
    ) -> bool:
        """
        向目标 Agent 发送消息
        用于 Multi-agent Teams 的跨节点通信
        """
        payload = {
            "type": "agent_message",
            "target_agent": target_agent,
            "sender": sender or "unknown",
            "content": message,
            "timestamp": time.time(),
        }
        # 广播到所有节点（目标 Agent 可能在任何节点上）
        self.broadcast(payload)
        return True

    def register_agent(self, agent_id: str, capabilities: List[str]):
        """
        注册 Agent 到网络
        让其他节点知道这个 Agent 的存在和能力
        """
        with self._lock:
            self._local_agents = getattr(self, "_local_agents", {})
            self._local_agents[agent_id] = {
                "capabilities": capabilities,
                "registered_at": time.time(),
            }

    def discover_agents(self, capability: Optional[str] = None) -> List[str]:
        """
        发现网络中的 Agent
        可按能力过滤
        """
        agents = []
        # TODO: 从其他节点收集 Agent 信息
        with self._lock:
            local = getattr(self, "_local_agents", {})
            for agent_id, info in local.items():
                if capability is None or capability in info.get("capabilities", []):
                    agents.append(agent_id)
        return agents
