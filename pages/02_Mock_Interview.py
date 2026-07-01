"""模拟面试页面 — 多轮面试模拟 + 实时打分 + 最终报告。

功能：
- 配置面试参数（主题、难度、题数）
- 多轮问答（面试官追问）
- 结构化打分（技术准确度、理解深度、表达清晰度、实例运用）
- 最终报告（雷达图 + 分析 + 建议）
"""

import streamlit as st

st.title("🎤 模拟面试")
st.markdown("体验真实的 LangChain 技术面试，AI 面试官出题并给出专业反馈。")

# 面试配置
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.selectbox("面试主题", ["全面综合", "Agents", "RAG", "Chains", "LCEL", "Memory", "LangGraph", "Tools", "部署与生产"])
with col2:
    difficulty = st.selectbox("难度", ["初级", "中级", "高级"])
with col3:
    question_count = st.selectbox("题目数量", [3, 5, 8, 10], index=1)

if st.button("🚀 开始面试", type="primary", use_container_width=True):
    st.session_state.interview_started = True
    st.session_state.interview_messages = []
    st.session_state.interview_question_index = 0
    st.rerun()

# 面试进行中
if st.session_state.get("interview_started"):
    st.divider()
    st.info("🏗️ 模拟面试 Agent 将在 Phase 4 中实现。")
    st.markdown(f"**配置**：{topic} / {difficulty} / {question_count} 题")
    st.markdown("面试消息将在此处展示...")

# 侧边栏
with st.sidebar:
    st.markdown("### 📋 面试历史")
    st.caption("暂无记录")
