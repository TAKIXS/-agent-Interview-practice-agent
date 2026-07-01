"""模拟面试页面 — 多轮面试 + 实时打分 + 最终报告。"""

import json
import streamlit as st

# ============================================================================
# 页面初始化
# ============================================================================
st.set_page_config(page_title="模拟面试", page_icon="🎤")

from src.utils.session import init_session_state
init_session_state()

st.title("🎤 模拟面试")
st.markdown("真实面试体验 — AI 面试官出题、追问、打分、给出专业反馈。")

# ============================================================================
# 初始化 Agent（缓存）
# ============================================================================

@st.cache_resource
def get_interview_agent():
    from src.llm.manager import ModelManager
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.interview_agent import InterviewAgent

    mgr = ModelManager()
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""

    return InterviewAgent(llm=mgr.llm, checkpointer=cm.get_checkpointer(), memory_context=ctx), cm


try:
    agent, conv_mgr = get_interview_agent()
    agent_ready = True
except Exception as e:
    agent_ready = False
    st.error(f"Agent 初始化失败: {e}")

# ============================================================================
# Session State 初始化
# ============================================================================
if "interview_phase" not in st.session_state:
    st.session_state.interview_phase = "setup"  # setup | interviewing | done
if "interview_thread" not in st.session_state:
    st.session_state.interview_thread = None
if "interview_messages" not in st.session_state:
    st.session_state.interview_messages = []
if "interview_scores" not in st.session_state:
    st.session_state.interview_scores = []
if "interview_config" not in st.session_state:
    st.session_state.interview_config = {}

# ============================================================================
# Phase: SETUP — 配置面试参数
# ============================================================================

if st.session_state.interview_phase == "setup":
    st.markdown("### 配置面试参数")

    col1, col2, col3 = st.columns(3)
    with col1:
        topic = st.selectbox(
            "面试主题",
            ["Java + Agent 综合", "Java 后端", "Agent 技术", "Java 并发", "Spring 框架", "JVM", "多 Agent 系统"],
        )
    with col2:
        difficulty = st.selectbox("难度", ["初级", "中级", "高级"])
    with col3:
        num_q = st.selectbox("题目数量", [3, 5, 8], index=1)

    if st.button("🚀 开始面试", type="primary", use_container_width=True, disabled=not agent_ready):
        with st.spinner("面试官准备中..."):
            thread_id = conv_mgr.new_thread_id()
            result = agent.start(thread_id, topic, difficulty, num_q)

        st.session_state.interview_thread = thread_id
        st.session_state.interview_config = {"topic": topic, "difficulty": difficulty, "num": num_q}
        st.session_state.interview_phase = "interviewing"

        # 提取面试官消息
        ai_msgs = [m for m in result.get("messages", []) if hasattr(m, "content") and m.type == "ai"]
        if ai_msgs:
            st.session_state.interview_messages = [
                {"role": "assistant", "content": str(ai_msgs[-1].content)}
            ]
        st.rerun()

# ============================================================================
# Phase: INTERVIEWING — 面试进行中
# ============================================================================

elif st.session_state.interview_phase == "interviewing":
    # 显示对话
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("score"):
                with st.expander("📊 评分详情"):
                    s = msg["score"]
                    cols = st.columns(4)
                    cols[0].metric("技术准确度", f"{s.get('technical_accuracy', 0):.1f}")
                    cols[1].metric("理解深度", f"{s.get('depth', 0):.1f}")
                    cols[2].metric("表达清晰", f"{s.get('clarity', 0):.1f}")
                    cols[3].metric("实例运用", f"{s.get('examples', 0):.1f}")
                    st.caption(f"综合: {s.get('overall', 0):.1f}/10")

    # 检查是否完成
    state = agent.get_state(st.session_state.interview_thread) if agent_ready else None
    is_complete = False
    if state and state.values:
        is_complete = state.values.get("interview_complete", False)
        scores = state.values.get("scores", [])
        current_q = state.values.get("current_question_index", 0)
        total_q = state.values.get("total_questions", 0)

        # 显示进度
        if total_q:
            progress_text = f"第 {min(current_q, total_q)} / {total_q} 题"
            if scores:
                avg = sum(s.get("overall", 0) for s in scores) / len(scores)
                progress_text += f"  |  均分: {avg:.1f}"
            st.progress(min(current_q / total_q, 1.0), text=progress_text)

    if is_complete:
        st.session_state.interview_phase = "done"
        st.rerun()

    # 输入回答
    if answer := st.chat_input("输入你的回答...", disabled=not agent_ready):
        st.session_state.interview_messages.append({"role": "user", "content": answer})

        with st.spinner("面试官评估中..."):
            result = agent.answer(st.session_state.interview_thread, answer)

        # 提取面试官回复
        ai_msgs = [m for m in result.get("messages", []) if hasattr(m, "content") and m.type == "ai"]
        if ai_msgs:
            for m in ai_msgs:
                content = str(m.content)
                # 判断是评分反馈还是问题
                st.session_state.interview_messages.append({
                    "role": "assistant",
                    "content": content,
                })

        # 提取最新分数
        if state and state.values:
            new_scores = state.values.get("scores", [])
            if new_scores:
                st.session_state.interview_messages[-1]["score"] = new_scores[-1]

        st.rerun()

# ============================================================================
# Phase: DONE — 面试完成
# ============================================================================

elif st.session_state.interview_phase == "done":
    st.success("🎉 面试完成！")

    # 显示完整对话回顾
    st.markdown("### 📋 面试回顾")
    for i, msg in enumerate(st.session_state.interview_messages):
        role_label = "👤 你" if msg["role"] == "user" else "🎤 面试官"
        with st.chat_message(msg["role"]):
            st.markdown(f"**{role_label}**\n\n{msg['content']}")
            if msg.get("score"):
                st.caption(f"得分: {msg['score'].get('overall', 0):.1f}/10")

    st.divider()

    col_r, col_n = st.columns(2)
    with col_r:
        if st.button("🔄 再来一次", use_container_width=True):
            st.session_state.interview_phase = "setup"
            st.session_state.interview_messages = []
            st.session_state.interview_scores = []
            st.session_state.interview_thread = None
            st.session_state.interview_config = {}
            st.rerun()
    with col_n:
        if st.button("🏠 返回首页", use_container_width=True):
            st.switch_page("app.py")

# ============================================================================
# 侧边栏
# ============================================================================
with st.sidebar:
    st.markdown("### 📋 面试信息")
    cfg = st.session_state.interview_config
    if cfg:
        st.markdown(f"**主题**: {cfg.get('topic')}")
        st.markdown(f"**难度**: {cfg.get('difficulty')}")
        st.markdown(f"**题数**: {cfg.get('num')}")
    else:
        st.caption("尚未开始")

    st.divider()

    if st.session_state.interview_phase != "setup":
        if st.button("⏹️ 结束面试", use_container_width=True):
            st.session_state.interview_phase = "done"
            st.rerun()
