#!/bin/bash
# AI-TP OS 启动脚本 (修复版)
# 作者: QClaw Agent
# 日期: 2026-06-22

echo "🚀 启动 AI-TP OS..."
echo ""

# 检查 Python 环境
echo "【1. 检查 Python 环境】"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
python3 --version
echo ""

# 检查虚拟环境
echo "【2. 检查虚拟环境】"
if [ ! -d "venv" ]; then
    echo "⚠️  虚拟环境不存在，创建中..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境
echo "【3. 激活虚拟环境】"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi
echo "✅ 虚拟环境已激活"
echo ""

# 升级 pip
echo "【4. 升级 pip】"
pip install --upgrade pip
echo ""

# 安装依赖
echo "【5. 安装依赖】"
echo "这可能需要 5-10 分钟，请耐心等待..."
pip install -e ".[all]"
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    echo "   请检查网络连接或手动安装"
    exit 1
fi
echo "✅ 依赖安装完成"
echo ""

# 检查配置文件
echo "【6. 检查配置文件】"
if [ ! -f "ai-tp-config.yaml" ]; then
    echo "⚠️  ai-tp-config.yaml 不存在，创建默认配置..."
    cat > ai-tp-config.yaml << 'EOF'
# AI-TP OS 默认配置
compute:
  backend: "ollama"
  ollama_host: "http://localhost:11434"
  default_model: "qwen2.5:0.5b"

storage:
  backend: "sqlite"
  sqlite_path: "/home/node/.openclaw/workspace/ai-tp-os/data/ai-tp.db"

network:
  enabled: false
  mode: "local"
EOF
    echo "✅ 默认配置已创建"
else
    echo "✅ 配置文件已存在"
fi
echo ""

# 创建必要目录
echo "【7. 创建必要目录】"
mkdir -p data models logs
echo "✅ 目录已创建"
echo ""

# 检查 Ollama (可选)
echo "【8. 检查 Ollama】"
if command -v ollama &> /dev/null; then
    echo "✅ Ollama 已安装"
    ollama --version
else
    echo "⚠️  Ollama 未安装（可选，但推荐）"
    echo "   安装方法: curl -fsSL https://ollama.com/install.sh | sh"
fi
echo ""

# 启动系统
echo "【9. 启动系统】"
echo "选择启动模式:"
echo "  1. CLI 模式 (命令行)"
echo "  2. Web UI 模式 (浏览器)"
echo "  3. Docker 模式 (容器)"
read -p "请选择 (1/2/3): " mode

if [ "$mode" = "1" ]; then
    echo ""
    echo "启动 CLI..."
    python3 core/cli.py status
elif [ "$mode" = "2" ]; then
    echo ""
    echo "启动 Web UI..."
    echo "请在浏览器中打开: http://localhost:8501"
    streamlit run apps/starter_ai_agents/ai_travel_agent/app.py
elif [ "$mode" = "3" ]; then
    echo ""
    echo "启动 Docker..."
    docker-compose up -d
    docker-compose ps
else
    echo "❌ 无效选择"
    exit 1
fi

echo ""
echo "🎉 AI-TP OS 启动完成！"
echo ""
echo "📁 查看修复报告: cat REPAIR_REPORT.md"
