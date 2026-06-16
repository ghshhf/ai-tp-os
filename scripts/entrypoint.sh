#!/bin/bash
# AI-TP OS - 容器入口脚本
# 以底层系统为本体，启动应用层服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI-TP OS 启动中...${NC}"
echo -e "${BLUE}========================================${NC}"

# 初始化环境
export AI_TP_HOME=${AI_TP_HOME:-/ai-tp-os}
export AI_TP_DATA_DIR=${AI_TP_DATA_DIR:-/data}
export AI_TP_MODELS_DIR=${AI_TP_MODELS_DIR:-/models}
export AI_TP_STORAGE_DIR=${AI_TP_STORAGE_DIR:-/storage}

# 创建必要目录
mkdir -p "$AI_TP_DATA_DIR" "$AI_TP_MODELS_DIR" "$AI_TP_STORAGE_DIR"

# 加载 .env 文件
if [ -f "$AI_TP_HOME/.env" ]; then
    echo -e "${GREEN}[INFO]${NC} 加载环境变量..."
    set -a
    source "$AI_TP_HOME/.env"
    set +a
fi

# 启动 Ollama 服务（如果安装了）
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}[INFO]${NC} 启动 Ollama 服务..."
    OLLAMA_HOST=${OLLAMA_HOST:-0.0.0.0:11434}
    export OLLAMA_HOST
    export OLLAMA_MODELS=${OLLAMA_MODELS:-$AI_TP_MODELS_DIR}
    
    # 后台启动 Ollama
    ollama serve &
    OLLAMA_PID=$!
    
    # 等待 Ollama 就绪
    echo -e "${YELLOW}[WAIT]${NC} 等待 Ollama 就绪..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo -e "${GREEN}[OK]${NC} Ollama 已就绪"
            break
        fi
        sleep 1
    done
    
    # 预拉取默认模型
    DEFAULT_MODEL=${OLLAMA_MODEL:-llama3.2}
    if ! ollama list | grep -q "$DEFAULT_MODEL"; then
        echo -e "${YELLOW}[INFO]${NC} 预拉取模型: $DEFAULT_MODEL"
        ollama pull "$DEFAULT_MODEL" || echo -e "${YELLOW}[WARN]${NC} 模型拉取失败，将在首次使用时重试"
    fi
fi

# 初始化 SQLite 数据库
if [ "$AI_TP_STORAGE_BACKEND" = "sqlite" ] || [ -z "$AI_TP_STORAGE_BACKEND" ]; then
    SQLITE_DB=${SQLITE_DB_PATH:-$AI_TP_DATA_DIR/ai-tp.db}
    echo -e "${GREEN}[INFO]${NC} 初始化 SQLite 数据库: $SQLITE_DB"
    mkdir -p "$(dirname "$SQLITE_DB")"
fi

# 启动网络发现服务（如果启用）
if [ "$AI_TP_NETWORK_ENABLED" = "true" ]; then
    echo -e "${GREEN}[INFO]${NC} 启动网络发现服务..."
    # TODO: 启动 ai-tp-discovery
fi

# 启动 Redis（如果配置了）
if [ "$AI_TP_STORAGE_BACKEND" = "redis" ]; then
    echo -e "${GREEN}[INFO]${NC} 启动 Redis 服务..."
    redis-server --daemonize yes --dir "$AI_TP_DATA_DIR"
fi

# 显示系统信息
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  AI-TP OS 启动完成!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}系统信息:${NC}"
echo -e "  工作目录: $AI_TP_HOME"
echo -e "  数据目录: $AI_TP_DATA_DIR"
echo -e "  模型目录: $AI_TP_MODELS_DIR"
echo -e "  存储目录: $AI_TP_STORAGE_DIR"
echo ""
echo -e "${BLUE}服务端口:${NC}"
echo -e "  Ollama API:  http://localhost:11434"
echo -e "  应用服务:    http://localhost:3000"
echo -e "  AI-TP Gateway: http://localhost:8080"
echo ""
echo -e "${BLUE}常用命令:${NC}"
echo -e "  ai-tp status      - 查看系统状态"
echo -e "  ai-tp model list  - 列出本地模型"
echo -e "  ai-tp run <app>   - 运行应用"
echo -e "  ai-tp storage     - 存储管理"
echo ""

# 执行传入的命令或进入交互式 shell
if [ $# -eq 0 ]; then
    echo -e "${GREEN}进入交互式 shell...${NC}"
    exec bash
else
    echo -e "${GREEN}执行命令: $@${NC}"
    exec "$@"
fi
