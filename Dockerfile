# AI-TP OS - 统一容器镜像
# 基于底层 glibc-packages 构建系统，整合 awesome-llm-apps 应用层

FROM ubuntu:24.04

LABEL maintainer="AI-TP OS Team"
LABEL description="AI-TP OS: AI-Native Decentralized OS with 100+ LLM Apps"

# 禁用交互式配置
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 基础系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    cmake \
    pkg-config \
    libssl-dev \
    libffi-dev \
    python3-dev \
    rustc \
    cargo \
    golang-go \
    jq \
    tmux \
    htop \
    neofetch \
    sqlite3 \
    libsqlite3-dev \
    redis-tools \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Ollama（本地 LLM 推理后端）
RUN curl -fsSL https://ollama.com/install.sh | sh

# 安装 Python 包管理器 uv（更快更可靠）
RUN pip3 install --break-system-packages uv

# 创建工作目录
WORKDIR /ai-tp-os

# 复制核心依赖文件
COPY pyproject.toml ./
COPY ai-tp-config.yaml ./
COPY .env.example ./

# 创建 Python 虚拟环境并安装依赖
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# 安装 Node.js 全局工具
RUN npm install -g @anthropic-ai/claude-code

# 暴露端口
# 11434: Ollama API
# 3000: 应用层服务
# 8080: AI-TP Gateway
EXPOSE 11434 3000 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# 启动脚本
COPY scripts/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
