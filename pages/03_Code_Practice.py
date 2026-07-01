"""代码实战页面 — 动手写 LangChain 代码 + 在线执行 + AI 评审。

功能：
- 按难度/主题筛选练习题
- 在线代码编辑器
- 安全代码执行（subprocess sandbox）
- AI 代码评审（正确性、效率、最佳实践）
- 渐进式提示
"""

import streamlit as st

st.title("💻 代码实战")
st.markdown("动手编写 LangChain 代码，在线执行并获得 AI 评审反馈。")

# 侧边栏 — 习题选择
with st.sidebar:
    st.markdown("### 📋 习题列表")
    st.selectbox("难度", ["初级", "中级", "高级"], key="code_difficulty")
    st.selectbox("主题", ["全部", "核心概念", "Chains", "Agents", "RAG", "LCEL", "Memory", "LangGraph"], key="code_topic")
    st.divider()

# 习题区
col_desc, col_code = st.columns([1, 1])

with col_desc:
    st.markdown("### 📖 练习说明")
    st.info("🏗️ 代码实战 Agent 将在 Phase 5 中实现。")
    st.markdown("*请从侧边栏选择一道练习题...*")

with col_code:
    st.markdown("### ✏️ 代码编辑区")
    code = st.text_area(
        "编写你的 LangChain 代码",
        height=300,
        placeholder="# 在此处编写代码...\nfrom langchain_core.prompts import ChatPromptTemplate\n\n# TODO: 实现你的代码",
        key="code_editor",
    )
    col_run, col_submit = st.columns(2)
    with col_run:
        st.button("▶️ 运行代码", use_container_width=True)
    with col_submit:
        st.button("📊 提交评审", type="primary", use_container_width=True)

st.divider()
st.markdown("### 📊 执行输出")
st.code("# 输出将在此处显示...", language="text")
