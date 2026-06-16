# AI-TP OS

AI-Native Decentralized Operating System with 100+ LLM Apps

以底层系统为本体，整合应用层的 AI 原生去中心化操作系统。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (100+ LLM Apps)                    │
│  Starter AI Agents / Advanced AI Agents / Multi-agent ...  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  AI-TP OS 系统层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  计算管理器  │  │  存储管理器  │  │  网络管理器  │        │
│  │ Ollama      │  │ SQLite      │  │ P2P Discovery│        │
│  │ LiteLLM     │  │ Redis       │  │ NAT Traversal│        │
│  │ LocalAI     │  │ Unified API │  │ Agent Mesh   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    硬件层                                    │
│  手机 / 电脑 / IoT / 服务器 / 路由器                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 使用 Docker（推荐）

```bash
# 克隆仓库
git clone https://github.com/ghshhf/ai-tp-os.git
cd ai-tp-os

# 启动系统
docker-compose up -d

# 查看状态
docker-compose exec ai-tp-core ai-tp status

# 运行应用
docker-compose exec ai-tp-core ai-tp run ai_travel_agent
```

### 2. 使用 Dev Container

在 VS Code 中打开项目，点击 "Reopen in Container"。

### 3. 本地安装

```bash
# 安装依赖
pip install -e .

# 初始化
ai-tp init

# 下载模型
ai-tp model pull llama3.2

# 运行应用
ai-tp run ai_travel_agent
```

---

## 核心特性

### 本地推理优先
- 默认使用 Ollama 本地推理
- 支持 llama3.2、qwen2.5 等开源模型
- 云 API 作为备用（OpenAI、Claude、Gemini）

### 统一存储层
- Agent 记忆共享
- 对话历史持久化
- RAG 文档管理
- 支持 SQLite、Redis、内存后端

### P2P 网络层
- 节点自动发现
- Agent 跨设备通信
- NAT 穿透
- 去中心化中继

### 统一配置
- 单文件配置 (`ai-tp-config.yaml`)
- 环境变量覆盖
- 多环境支持

---

## 命令行工具

```bash
# 系统管理
ai-tp status              # 查看系统状态
ai-tp init                # 初始化环境
ai-tp config-reload       # 重新加载配置

# 模型管理
ai-tp model list          # 列出本地模型
ai-tp model pull <name>   # 下载模型
ai-tp model rm <name>     # 删除模型

# 应用管理
ai-tp run <app_name>      # 运行应用
ai-tp run ai_travel_agent # 运行旅行 Agent
ai-tp run ai_music_generator  # 运行音乐生成器

# 存储管理
ai-tp storage list        # 列出存储键
ai-tp storage get <key>   # 读取数据
ai-tp storage put <key> <value>  # 存储数据
ai-tp storage del <key>   # 删除数据
```

---

## 应用目录

### Starter AI Agents（入门级）

| 应用 | 描述 | 命令 |
|------|------|------|
| AI Travel Agent | 旅行规划助手 | `ai-tp run ai_travel_agent` |
| AI Music Generator | 音乐创作助手 | `ai-tp run ai_music_generator` |
| AI Meme Generator | 梗图生成器 | `ai-tp run ai_meme_generator` |

### Advanced AI Agents（高级）

| 应用 | 描述 | 状态 |
|------|------|------|
| AI Deep Research | 深度研究 Agent | 开发中 |
| AI VC Due Diligence | 投资尽调 Agent | 开发中 |
| AI Financial Coach | 财务顾问 Agent | 开发中 |

### Multi-agent Teams（多智能体）

| 应用 | 描述 | 状态 |
|------|------|------|
| AI Competitor Intelligence | 竞品情报团队 | 开发中 |
| AI Finance Team | 金融分析团队 | 开发中 |
| AI Recruitment Team | 招聘团队 | 开发中 |

---

## 配置

### 环境变量 (.env)

```bash
# 复制模板
cp .env.example .env

# 编辑配置
vim .env
```

### 配置文件 (ai-tp-config.yaml)

```yaml
inference:
  default_backend: ollama
  backends:
    ollama:
      enabled: true
      host: http://localhost:11434
      default_model: llama3.2

storage:
  backend: sqlite
  shared: true

network:
  enabled: true
  mode: hybrid
```

---

## 开发

### 项目结构

```
ai-tp-os/
├── core/                    # 底层系统核心
│   ├── config/             # 配置管理
│   ├── compute/            # 计算层 (Ollama, LiteLLM)
│   ├── storage/            # 存储层 (SQLite, Redis)
│   ├── network/            # 网络层 (P2P Discovery)
│   └── cli.py              # 命令行接口
├── apps/                    # 应用层
│   ├── starter_ai_agents/  # 入门级 Agent
│   ├── advanced_ai_agents/ # 高级 Agent
│   ├── multi_agent_teams/  # 多智能体团队
│   ├── rag_tutorials/      # RAG 教程
│   ├── voice_ai_agents/    # 语音 Agent
│   └── mcp_ai_agents/      # MCP Agent
├── scripts/                 # 工具脚本
├── docs/                    # 文档
├── Dockerfile               # 容器镜像
├── docker-compose.yml       # 编排配置
├── pyproject.toml           # Python 依赖
├── ai-tp-config.yaml        # 系统配置
└── .env.example             # 环境变量模板
```

### 添加新应用

1. 在 `apps/<category>/<app_name>/` 创建目录
2. 创建 `app.py` 作为入口
3. 使用 `core.compute.ollama_client.OllamaClient` 进行推理
4. 使用 `core.storage.unified_storage.UnifiedStorage` 进行存储
5. 在 `ai-tp-config.yaml` 注册应用

---

## 路线图

### Phase 1: 基础环境（已完成）
- [x] 统一 Docker 环境
- [x] Ollama 本地推理集成
- [x] 统一存储层 (SQLite)
- [x] 统一配置系统
- [x] CLI 工具

### Phase 2: 应用整合（进行中）
- [x] Starter AI Agents 模板
- [ ] Advanced AI Agents 模板
- [ ] Multi-agent Teams 模板
- [ ] RAG Tutorials 模板

### Phase 3: 分布式能力
- [ ] P2P 网络发现
- [ ] Agent 跨设备通信
- [ ] 分布式任务调度
- [ ] 模型 P2P 分发

### Phase 4: 系统完善
- [ ] 安全加密
- [ ] 监控告警
- [ ] 性能优化
- [ ] 文档完善

---

## 许可证

Apache-2.0

---

## 维护者

@ghshhf
