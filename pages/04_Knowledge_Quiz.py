"""知识测验页面 — AI 自动出题 + 逐题作答 + 成绩报告。"""

import json
import streamlit as st

# ============================================================================
st.set_page_config(page_title="知识测验", page_icon="📝")

from src.utils.session import init_session_state
init_session_state()

st.title("📝 知识测验")
st.markdown("AI 自动出题 — 选择题 + 即时反馈 + 成绩报告。")

# ============================================================================
# Agent 缓存
# ============================================================================

@st.cache_resource
def get_quiz_agent():
    from src.llm.manager import ModelManager
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.quiz_agent import QuizAgent

    mgr = ModelManager()
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""
    return QuizAgent(llm=mgr.llm, checkpointer=cm.get_checkpointer(), memory_context=ctx), cm


try:
    agent, conv_mgr = get_quiz_agent()
    agent_ready = True
except Exception as e:
    agent_ready = False
    st.error(f"Agent 初始化失败: {e}")

# ============================================================================
# Session State
# ============================================================================
if "quiz_phase" not in st.session_state:
    st.session_state.quiz_phase = "setup"
if "quiz_thread" not in st.session_state:
    st.session_state.quiz_thread = None
if "quiz_messages" not in st.session_state:
    st.session_state.quiz_messages = []
if "quiz_config" not in st.session_state:
    st.session_state.quiz_config = {}
if "quiz_current_q" not in st.session_state:
    st.session_state.quiz_current_q = None  # 当前题目数据

# ============================================================================
# Phase: SETUP
# ============================================================================
if st.session_state.quiz_phase == "setup":
    st.markdown("### 配置测验")

    c1, c2, c3 = st.columns(3)
    with c1:
        topic = st.selectbox("测验主题",
            ["Java + Agent 综合", "Java 基础", "JVM", "并发编程", "Spring", "Agent 基础", "Agent 工具", "RAG", "多 Agent"],
        )
    with c2:
        difficulty = st.selectbox("难度", ["初级", "中级", "高级"], index=1)
    with c3:
        count = st.selectbox("题数", [5, 10, 15], index=0)

    if st.button("🚀 开始测验", type="primary", use_container_width=True, disabled=not agent_ready):
        with st.spinner("AI 出题中..."):
            tid = conv_mgr.new_thread_id()
            result = agent.start(tid, topic, difficulty, count)

        st.session_state.quiz_thread = tid
        st.session_state.quiz_config = {"topic": topic, "difficulty": difficulty, "count": count}
        st.session_state.quiz_phase = "answering"
        st.session_state.quiz_messages = []

        # 获取第一道题
        state = agent.get_state(tid)
        if state and state.values:
            questions = state.values.get("questions", [])
            if questions:
                st.session_state.quiz_current_q = 0
                q = questions[0]
                st.session_state.quiz_messages = [{
                    "role": "assistant",
                    "content": f"**第 1/{count} 题** ({q.get('topic','')})\n\n{q['question']}\n\n" + "\n".join(q['options']),
                }]
        st.rerun()

# ============================================================================
# Phase: ANSWERING
# ============================================================================
elif st.session_state.quiz_phase == "answering":
    # 显示之前的消息
    for msg in st.session_state.quiz_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 检查是否完成
    state = agent.get_state(st.session_state.quiz_thread) if agent_ready else None
    if state and state.values:
        complete = state.values.get("quiz_complete", False)
        current = state.values.get("current_question_index", 0)
        total = state.values.get("total_questions", 0)
        scores = state.values.get("scores", [])
        questions = state.values.get("questions", [])

        if total:
            correct = sum(scores)
            st.progress(current / total, text=f"进度: {current}/{total}  |  正确: {correct}/{len(scores) if scores else 0}")

        if complete:
            st.session_state.quiz_phase = "done"
            st.rerun()

        if current < total:
            # 显示当前题目选项
            q = questions[current] if current < len(questions) else None
            if q:
                st.markdown("### 请选择答案")
                option_labels = [opt.split(". ", 1)[-1] for opt in q["options"]]
                choice = st.radio(
                    f"第 {current+1} 题：{q['question']}",
                    option_labels,
                    index=None,
                    key=f"q_{current}",
                )

                if choice is not None and st.button("提交答案", type="primary", use_container_width=True):
                    selected_idx = option_labels.index(choice)
                    # 记录选择
                    if len(st.session_state.quiz_messages) == current * 2 + 1:
                        st.session_state.quiz_messages.append({"role": "user", "content": choice})

                    with st.spinner("评分中..."):
                        result = agent.answer(st.session_state.quiz_thread, selected_idx)

                    # 获取反馈和下一题
                    state2 = agent.get_state(st.session_state.quiz_thread)
                    if state2 and state2.values:
                        new_msgs = [m for m in state2.values.get("messages", [])[-3:]
                                    if hasattr(m, "content") and m.type == "ai"]
                        for m in new_msgs:
                            if m.content not in [x.get("content", "") for x in st.session_state.quiz_messages]:
                                st.session_state.quiz_messages.append({
                                    "role": "assistant", "content": str(m.content),
                                })
                        if state2.values.get("quiz_complete"):
                            st.session_state.quiz_phase = "done"
                    st.rerun()

# ============================================================================
# Phase: DONE
# ============================================================================
elif st.session_state.quiz_phase == "done":
    st.success("🎉 测验完成！")

    state = agent.get_state(st.session_state.quiz_thread) if agent_ready else None
    if state and state.values:
        scores = state.values.get("scores", [])
        total = state.values.get("total_questions", 5)
        correct = sum(scores)
        st.metric("正确率", f"{correct}/{total} ({correct/total*100:.0f}%)" if total else "N/A")

    for msg in st.session_state.quiz_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 再来一次", use_container_width=True):
            st.session_state.quiz_phase = "setup"
            st.session_state.quiz_messages = []
            st.session_state.quiz_thread = None
            st.session_state.quiz_config = {}
            st.session_state.quiz_current_q = None
            st.rerun()
    with c2:
        if st.button("🏠 返回首页", use_container_width=True):
            st.switch_page("app.py")
