"""模拟面试 — Apple 极简风格。"""

import streamlit as st
from dotenv import load_dotenv; load_dotenv()

st.set_page_config(page_title="Interview", page_icon="◈")
from src.utils.session import init_session_state
init_session_state()

st.html("""
<style>
#MainMenu, footer, .stDeployButton { display: none; }
h1 { font-size: 2rem !important; font-weight: 700 !important; color: #1D1D1F; }
.stButton > button {
    background: #0071E3; color: white; border: none; border-radius: 12px;
    padding: 0.6rem 1.5rem; font-weight: 500; transition: all 0.15s;
}
.stButton > button:hover { background: #0077ED; }
.stRadio > div { gap: 0.5rem; }
.stRadio label {
    background: #F5F5F7; border-radius: 10px; padding: 0.75rem 1rem;
    border: 1px solid #E8E8ED; cursor: pointer; width: 100%;
}
.stRadio label:hover { border-color: #0071E3; }
.chat-bubble {
    background: #F5F5F7; border-radius: 14px; padding: 1rem 1.25rem; margin: 0.5rem 0;
}
.metric-box {
    background: #F5F5F7; border-radius: 12px; padding: 1rem; text-align: center;
}
.metric-value { font-size: 1.5rem; font-weight: 700; color: #1D1D1F; }
.metric-label { font-size: 0.8rem; color: #86868B; }
</style>
""")

st.title("Interview")
st.html('<p style="color:#86868B;font-size:0.95rem;margin-bottom:1.5rem">AI 面试官 · 专业出题 · 实时打分 · 详细反馈</p>')

# Agent
@st.cache_resource
def get_interview():
    from src.llm.manager import ModelManager
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.interview_agent import InterviewAgent
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""
    return InterviewAgent(ModelManager().llm, cm.get_checkpointer(), ctx), cm

agent, cm = get_interview()

# State
for k in ["iv_phase", "iv_thread", "iv_msgs", "iv_cfg"]:
    if k not in st.session_state:
        st.session_state[k] = "setup" if k == "iv_phase" else (None if k == "iv_thread" else [] if k == "iv_msgs" else {})

# --- Setup ---
if st.session_state.iv_phase == "setup":
    st.html('<div style="max-width:480px;margin:2rem auto">')

    st.html('<p style="font-weight:600;color:#1D1D1F;margin-bottom:1rem">面试配置</p>')

    topic = st.selectbox("主题", ["Java + Agent 综合", "Java 后端", "Agent 技术", "Java 并发", "Spring", "JVM", "多 Agent"])
    difficulty = st.selectbox("难度", ["初级", "中级", "高级"], index=1)
    count = st.selectbox("题数", [3, 5, 8], index=1)

    st.html('<div style="height:1rem"></div>')

    if st.button("开始面试", type="primary", use_container_width=True):
        with st.spinner("准备中..."):
            tid = cm.new_thread_id()
            result = agent.start(tid, topic, difficulty, count)
        msgs = [m for m in result.get("messages", []) if hasattr(m, "content") and m.type == "ai"]
        st.session_state.iv_thread = tid
        st.session_state.iv_cfg = {"topic": topic, "difficulty": difficulty, "count": count}
        st.session_state.iv_msgs = [{"role": "assistant", "content": str(msgs[-1].content)}] if msgs else []
        st.session_state.iv_phase = "active"
        st.rerun()

    st.html('</div>')

# --- Active ---
elif st.session_state.iv_phase == "active":
    for msg in st.session_state.iv_msgs:
        role = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(msg["content"])

    state = agent.get_state(st.session_state.iv_thread)
    complete = state.values.get("interview_complete", False) if state and state.values else False

    if complete:
        st.session_state.iv_phase = "done"
        st.rerun()

    # 进度条
    if state and state.values:
        total = state.values.get("total_questions", 0)
        current = state.values.get("current_question_index", 0)
        scores = state.values.get("scores", [])
        avg = sum(s.get("overall", 0) for s in scores) / len(scores) if scores else 0
        st.progress(min(current / total, 1.0) if total else 0,
                     text=f"第 {min(current, total)}/{total} 题 · 均分 {avg:.1f}")

    if answer := st.chat_input("输入你的回答..."):
        st.session_state.iv_msgs.append({"role": "user", "content": answer})
        with st.spinner(""):
            result = agent.answer(st.session_state.iv_thread, answer)
        msgs = [m for m in result.get("messages", []) if hasattr(m, "content") and m.type == "ai"]
        for m in msgs:
            st.session_state.iv_msgs.append({"role": "assistant", "content": str(m.content)})
        st.rerun()

# --- Done ---
elif st.session_state.iv_phase == "done":
    st.success("面试完成")
    for msg in st.session_state.iv_msgs:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.markdown(msg["content"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("再来一次", use_container_width=True):
            for k in ["iv_phase", "iv_thread", "iv_msgs", "iv_cfg"]:
                st.session_state[k] = "setup" if k == "iv_phase" else (None if k == "iv_thread" else [] if k == "iv_msgs" else {})
            st.rerun()
    with c2:
        if st.button("返回首页", use_container_width=True):
            st.switch_page("app.py")

# 侧边栏
with st.sidebar:
    st.markdown("**Interview**")
    cfg = st.session_state.iv_cfg
    if cfg:
        st.caption(f"主题: {cfg.get('topic')}")
        st.caption(f"难度: {cfg.get('difficulty')}")
        st.caption(f"题数: {cfg.get('count')}")
    if st.session_state.iv_phase == "active":
        if st.button("结束", use_container_width=True):
            st.session_state.iv_phase = "done"
            st.rerun()
