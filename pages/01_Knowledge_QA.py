"""知识问答页面 — RAG 驱动的 LangChain 技术问答。

功能：
- 多轮对话（带历史上下文）
- 来源文档引用
- 主题分类过滤
"""

import streamlit as st

st.title("💬 知识问答")
st.markdown("问任何 LangChain 相关问题，我会从知识库中检索并回答。")

# 初始化聊天历史
if "qa_messages" not in st.session_state:
    st.session_state.qa_messages = []

# 显示历史消息
for msg in st.session_state.qa_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入区
if prompt := st.chat_input("输入你的 LangChain 问题..."):
    st.session_state.qa_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        st.info("🏗️ 知识问答 Agent 将在 Phase 3 中实现。当前为框架占位。")
        st.markdown(f"你问的是：_{prompt}_")

# 侧边栏 — 过滤
st.sidebar.markdown("### 🔍 主题过滤")
st.sidebar.selectbox("选择知识领域", ["全部", "核心概念", "LCEL", "Chains", "Agents", "Tools", "Memory", "RAG", "LangGraph", "回调/流式", "部署", "最佳实践"], key="qa_filter")
