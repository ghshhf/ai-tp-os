"""
AI-TP OS - AI Music Generator (整合版)
以底层系统为本体，使用统一推理接口
"""

import streamlit as st
from core.compute.ollama_client import OllamaClient
from core.config.settings import get_config

# 页面配置
st.set_page_config(
    page_title="AI Music Generator - AI-TP OS",
    page_icon="🎵",
    layout="wide",
)

# 初始化
@st.cache_resource
def get_inference():
    return OllamaClient()

inference = get_inference()

st.title("🎵 AI Music Generator")
st.caption("Powered by AI-TP OS - 本地推理，创意无限")

# 参数配置
col1, col2 = st.columns(2)

with col1:
    genre = st.selectbox(
        "音乐风格",
        ["流行", "古典", "爵士", "电子", "摇滚", "民谣", "R&B", "嘻哈"],
    )
    mood = st.select_slider(
        "情绪",
        options=["忧伤", "平静", "轻松", "欢快", "激昂"],
        value="轻松",
    )

with col2:
    tempo = st.slider("速度 (BPM)", 60, 180, 120)
    duration = st.slider("时长 (秒)", 30, 300, 60)

# 额外描述
description = st.text_area(
    "补充描述",
    placeholder="描述你想要的音乐感觉，例如：像夏日海边的微风...",
    height=100,
)

# 生成按钮
if st.button("🎼 生成音乐描述", type="primary"):
    with st.spinner("AI-TP OS 创作中..."):
        try:
            prompt = f"""你是一位音乐创作专家。请根据以下要求，生成一段详细的音乐创作描述：

风格：{genre}
情绪：{mood}
速度：{tempo} BPM
时长：{duration} 秒
补充描述：{description or '无'}

请提供：
1. 音乐的整体构思
2. 乐器编排建议
3. 旋律走向描述
4. 和声进行建议
5. 制作技巧提示
"""

            response = inference.generate(
                model="llama3.2",
                prompt=prompt,
                system="你是一个专业的音乐制作人，擅长用文字描述音乐创作。",
            )

            content = response.get("response", "")
            
            st.success("创作完成！")
            st.markdown(content)
            
            # 保存到历史
            if "history" not in st.session_state:
                st.session_state.history = []
            st.session_state.history.append({
                "genre": genre,
                "mood": mood,
                "description": content,
            })
            
        except Exception as e:
            st.error(f"生成错误: {e}")

# 历史记录
if "history" in st.session_state and st.session_state.history:
    st.divider()
    st.subheader("📜 创作历史")
    for i, item in enumerate(st.session_state.history[-5:]):
        with st.expander(f"{i+1}. {item['genre']} - {item['mood']}"):
            st.markdown(item["description"])

st.caption("🚀 AI-TP OS | 本地推理 | 隐私保护")
