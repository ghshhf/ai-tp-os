"""
AI-TP OS - AI Meme Generator (整合版)
以底层系统为本体，使用统一推理接口
"""

import streamlit as st
from core.compute.ollama_client import OllamaClient

# 页面配置
st.set_page_config(
    page_title="AI Meme Generator - AI-TP OS",
    page_icon="😂",
    layout="wide",
)

# 初始化
@st.cache_resource
def get_inference():
    return OllamaClient()

inference = get_inference()

st.title("😂 AI Meme Generator")
st.caption("Powered by AI-TP OS - 本地推理，欢乐无限")

# 模板选择
template = st.selectbox(
    "选择模板风格",
    [
        "自定义",
        "程序员梗",
        "职场日常",
        "学习痛苦",
        "AI 相关",
        "生活吐槽",
        "励志鸡汤",
    ],
)

# 主题输入
topic = st.text_input(
    "主题",
    placeholder="输入一个主题，例如：写代码遇到 bug",
)

# 风格选择
style = st.radio(
    "梗图风格",
    ["讽刺", "自嘲", "夸张", "冷幽默", "暖心"],
    horizontal=True,
)

# 生成按钮
if st.button("🎨 生成梗图文案", type="primary"):
    if not topic:
        st.warning("请输入一个主题")
    else:
        with st.spinner("AI-TP OS 创作中..."):
            try:
                prompt = f"""你是一位网络梗图文案大师。请根据以下要求，创作一个有趣的梗图文案：

模板风格：{template}
主题：{topic}
风格：{style}

请提供：
1. 梗图标题（简短有力）
2. 上方文字（设置场景）
3. 下方文字（笑点/反转）
4. 画面描述（用于生成图像的提示词）
5. 标签建议（3-5 个相关标签）

要求：
- 文案要简洁有力
- 符合中文网络文化
- 有共鸣感
"""

                response = inference.generate(
                    model="llama3.2",
                    prompt=prompt,
                    system="你是一个网络梗图创作专家，擅长创作让人会心一笑的文案。",
                )

                content = response.get("response", "")
                
                st.success("创作完成！")
                st.markdown(content)
                
                # 保存到历史
                if "meme_history" not in st.session_state:
                    st.session_state.meme_history = []
                st.session_state.meme_history.append({
                    "template": template,
                    "topic": topic,
                    "style": style,
                    "content": content,
                })
                
            except Exception as e:
                st.error(f"生成错误: {e}")

# 历史记录
if "meme_history" in st.session_state and st.session_state.meme_history:
    st.divider()
    st.subheader("📜 创作历史")
    for i, item in enumerate(st.session_state.meme_history[-5:]):
        with st.expander(f"{i+1}. {item['topic']} ({item['style']})"):
            st.markdown(item["content"])

st.caption("🚀 AI-TP OS | 本地推理 | 隐私保护")
