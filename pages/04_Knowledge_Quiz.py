"""知识测验页面 — AI 自动出题 + 选择题作答 + 即时反馈。

功能：
- 自动生成场景化选择题
- 逐题作答 + 即时正误判定
- 错题概念自动记录
- 最终成绩仪表盘
"""

import streamlit as st

st.title("📝 知识测验")
st.markdown("AI 自动生成 LangChain 知识测验，检验你的学习成果。")

# 测验配置
col1, col2, col3 = st.columns(3)
with col1:
    quiz_topic = st.selectbox("测验主题", ["全面综合", "Agents", "RAG", "Chains", "LCEL", "Memory", "LangGraph", "Tools"])
with col2:
    quiz_difficulty = st.selectbox("难度", ["初级", "中级", "高级"], index=1)
with col3:
    quiz_count = st.selectbox("题目数量", [5, 10, 15, 20], index=1)

if st.button("🚀 开始测验", type="primary", use_container_width=True):
    st.session_state.quiz_started = True
    st.session_state.quiz_questions = []
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.rerun()

if st.session_state.get("quiz_started"):
    st.divider()
    st.info("🏗️ 知识测验 Agent 将在 Phase 6 中实现。")
    st.markdown(f"**配置**：{quiz_topic} / {quiz_difficulty} / {quiz_count} 题")
    st.markdown("测验题目将在此处逐个展示...")

# 侧边栏
with st.sidebar:
    st.markdown("### 📊 测验统计")
    st.metric("历史最佳", "--")
    st.metric("平均分", "--")
    st.metric("已完成测验", "0")
