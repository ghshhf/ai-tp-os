"""
AI-TP OS - AI Travel Agent (整合版)
以底层系统为本体，使用统一推理和存储接口
"""

import streamlit as st
from core.compute.ollama_client import OllamaClient
from core.config.settings import get_config
from core.storage.unified_storage import UnifiedStorage

# 页面配置
st.set_page_config(
    page_title="AI Travel Agent - AI-TP OS",
    page_icon="🛫",
    layout="wide",
)

# 初始化 AI-TP OS 核心服务
@st.cache_resource
def get_services():
    config = get_config()
    inference = OllamaClient()
    storage = UnifiedStorage(config.storage)
    return inference, storage

inference, storage = get_services()

# 标题
st.title("🛫 AI Travel Agent")
st.caption("Powered by AI-TP OS - 本地推理优先，隐私保护")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    
    # 模型选择
    models = inference.list_models()
    model_names = [m["name"] for m in models] if models else ["llama3.2"]
    selected_model = st.selectbox("选择模型", model_names)
    
    # 旅行偏好
    st.subheader("旅行偏好")
    budget = st.selectbox("预算", ["经济", "中等", "豪华"])
    style = st.multiselect(
        "旅行风格",
        ["文化", "自然", "美食", "冒险", "休闲", "购物"],
        default=["文化", "美食"],
    )
    
    # 存储选项
    st.subheader("💾 记忆")
    save_memory = st.toggle("保存对话记忆", value=True)
    
    if st.button("🗑️ 清除记忆"):
        storage.delete("travel_agent_session", namespace="agent_memory")
        st.success("记忆已清除")

# 主界面
st.header("告诉我你的旅行计划")

destination = st.text_input("目的地", placeholder="例如：日本京都")
days = st.slider("天数", 1, 14, 3)
travelers = st.number_input("人数", 1, 10, 1)

# 加载历史对话
session_key = "travel_agent_session"
if "messages" not in st.session_state:
    history = storage.load_conversation(session_key)
    st.session_state.messages = history or []

# 显示对话历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 用户输入
if prompt := st.chat_input("描述你的旅行需求..."):
    # 构建系统提示
    system_prompt = f"""你是一位专业的旅行规划师。根据用户的需求，提供详细的旅行建议。

用户偏好：
- 预算：{budget}
- 风格：{", ".join(style)}
- 天数：{days} 天
- 人数：{travelers} 人

请提供：
1. 行程概览
2. 每日详细安排
3. 住宿推荐
4. 美食推荐
5. 实用贴士
"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # 添加历史消息
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # 添加当前消息
    messages.append({"role": "user", "content": prompt})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.write(prompt)
    
    # 调用 AI-TP OS 推理服务
    with st.chat_message("assistant"):
        with st.spinner("AI-TP OS 思考中..."):
            try:
                response = inference.chat(
                    model=selected_model,
                    messages=messages,
                )
                
                content = response.get("message", {}).get("content", "抱歉，我无法回答。")
                st.write(content)
                
                # 保存对话
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "assistant", "content": content})
                
                if save_memory:
                    storage.save_conversation(session_key, st.session_state.messages)
                    
            except Exception as e:
                st.error(f"推理错误: {e}")
                st.info("请确保 Ollama 服务已启动，或检查模型是否已下载。")

# 底部信息
st.divider()
st.caption("🚀 AI-TP OS | 本地推理 | 隐私保护 | 去中心化")
