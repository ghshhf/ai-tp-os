"""
AI-TP OS - Ollama 本地推理客户端
以底层系统为本体，为应用层提供统一的本地 LLM 推理能力

使用 urllib（标准库）替代 requests，零外部依赖。
"""

import json
import time
import urllib.request
import urllib.error
import ssl
from typing import Any, Dict, Iterator, List, Optional


class OllamaClient:
    """
    Ollama 本地推理客户端
    封装 Ollama HTTP API，提供与 OpenAI 兼容的接口
    """

    def __init__(self, host: str = "http://localhost:11434", timeout: int = 120):
        self.host = host.rstrip("/")
        self.timeout = timeout
        # 创建可复用的 SSL context
        self._ssl_context = ssl.create_default_context()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[bytes] = None,
        stream: bool = False,
    ):
        """
        发送 HTTP 请求，返回响应对象。
        stream=True 时返回原始 urllib.response 对象用于逐行读取。
        """
        url = f"{self.host}/api/{endpoint}"
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")

        try:
            resp = urllib.request.urlopen(
                req, timeout=self.timeout, context=self._ssl_context
            )
            return resp
        except urllib.error.HTTPError as e:
            # 将 HTTP 错误包装，让调用方可以处理
            raise RuntimeError(
                f"Ollama HTTP {e.code}: {e.reason} - {e.read().decode('utf-8', errors='replace')}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Ollama connection error: {e.reason}"
            ) from e

    def list_models(self) -> List[Dict[str, Any]]:
        """列出本地可用的模型"""
        resp = self._request("GET", "tags")
        body = resp.read().decode("utf-8")
        return json.loads(body).get("models", [])

    def pull_model(self, model: str, stream: bool = True) -> Iterator[str]:
        """拉取模型"""
        payload = json.dumps({"name": model, "stream": stream}).encode("utf-8")
        resp = self._request("POST", "pull", data=payload, stream=stream)

        if stream:
            for line in resp:
                decoded = line.decode("utf-8").strip()
                if decoded:
                    yield decoded
        else:
            yield resp.read().decode("utf-8")

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        生成文本（单次对话）
        兼容 OpenAI 的 completions 接口风格
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        if options:
            payload["options"] = options

        data = json.dumps(payload).encode("utf-8")
        resp = self._request("POST", "generate", data=data, stream=stream)

        if stream:
            return {"stream": resp

        return json.loads(resp.read().decode("utf-8"))

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        options: Optional[Dict] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        聊天对话（多轮）
        兼容 OpenAI 的 chat.completions 接口风格
        """
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        data = json.dumps(payload).encode("utf-8")
        resp = self._request("POST", "chat", data=data, stream=stream)

        if stream:
            return {"stream": resp

        return json.loads(resp.read().decode("utf-8"))

    def embeddings(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict] = None,
    ) -> List[float]:
        """
        获取文本嵌入向量
        用于 RAG 检索
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
        }
        if options:
            payload["options"] = options

        data = json.dumps(payload).encode("utf-8")
        resp = self._request("POST", "embeddings", data=data)
        return json.loads(resp.read().decode("utf-8")).get("embedding", [])

    def create_embedding(
        self,
        input: str,
        model: str = "nomic-embed-text",
    ) -> Dict[str, Any]:
        """
        OpenAI 兼容的 embeddings 接口
        """
        embedding = self.embeddings(model, input)
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": embedding,
                    "index": 0,
                }
            ],
            "model": model,
            "usage": {
                "prompt_tokens": len(input.split()),
                "total_tokens": len(input.split()),
            },
        }

    def create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        OpenAI 兼容的 chat.completions 接口
        让应用层可以无缝切换本地/云推理
        """
        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        result = self.chat(
            model=model,
            messages=messages,
            options=options,
            stream=stream,
        )

        if stream:
            return result

        # 转换为 OpenAI 格式
        message = result.get("message", {})
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": message.get("role", "assistant"),
                        "content": message.get("content", ""),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": (
                    result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                ),
            },
        }

    def health(self) -> bool:
        """检查 Ollama 服务是否健康"""
        try:
            resp = self._request("GET", "tags")
            resp.read()  # 消费响应体
            return True
        except Exception:
            return False


class InferenceEngine:
    """
    AI-TP OS 推理引擎
    统一管理本地和云推理后端
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.clients: Dict[str, Any] = {}
        self._init_clients()

    def _init_clients(self):
        """初始化推理客户端"""
        backends = self.config.get("backends", {})

        if backends.get("ollama", {}).get("enabled", False):
            ollama_cfg = backends["ollama"]
            self.clients["ollama"] = OllamaClient(
                host=ollama_cfg.get("host", "http://localhost:11434"),
                timeout=ollama_cfg.get("timeout", 120),
            )

        # TODO: 初始化其他后端 (OpenAI, Anthropic, Gemini)

    def get_client(self, backend: Optional[str] = None):
        """获取推理客户端"""
        if backend and backend in self.clients:
            return self.clients[backend]

        # 按 fallback 顺序查找可用后端
        fallback = self.config.get("fallback", {})
        if fallback.get("enabled"):
            for name in fallback.get("order", []):
                client = self.clients.get(name)
                if client and hasattr(client, "health") and client.health():
                    return client

        # 默认返回第一个可用客户端
        for client in self.clients.values():
            return client

        raise RuntimeError("No inference backend available")

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        backend: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        统一聊天接口
        应用层只需调用此方法，无需关心底层后端
        """
        client = self.get_client(backend)

        if isinstance(client, OllamaClient):
            model_name = model or self.config.get("backends", {}).get("ollama", {}).get("default_model", "llama3.2")
            result = client.chat(model=model_name, messages=messages, **kwargs)
            if "stream" in result:
                # 处理流式响应
                return self._handle_stream(result["stream"])
            return result.get("message", {}).get("content", "")

        # TODO: 处理其他后端
        raise NotImplementedError(f"Backend {backend} not implemented")

    def _handle_stream(self, stream) -> str:
        """处理流式响应"""
        chunks = []
        for line in stream:
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            else:
                line = line.decode("utf-8") if hasattr(line, "decode") else str(line)
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                chunks.append(chunk)
                if data.get("done"):
                    break
            except json.JSONDecodeError:
                continue
        return "".join(chunks)

    def embed(self, text: str, model: Optional[str] = None, backend: Optional[str] = None) -> List[float]:
        """统一嵌入接口"""
        client = self.get_client(backend)

        if isinstance(client, OllamaClient):
            embed_model = model or "nomic-embed-text"
            return client.embeddings(embed_model, text)

        raise NotImplementedError(f"Backend {backend} not implemented")

    def health_check(self) -> Dict[str, bool]:
        """检查所有后端健康状态"""
        return {
            name: client.health() if hasattr(client, "health") else True
            for name, client in self.clients.items()
        }
