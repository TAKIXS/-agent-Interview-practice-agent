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
def get_interview_agent(provider: str, model: str):
    from src.utils.session import get_shared_llm
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.interview_agent import InterviewAgent
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""
    return InterviewAgent(get_shared_llm(), cm.get_checkpointer(), ctx), cm

agent, cm = get_interview_agent(
    st.session_state.get("current_provider", ""),
    st.session_state.get("current_model", ""),
)

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
            try:
                result = agent.start(tid, topic, difficulty, count)
            except Exception as e:
                st.error(f"请求失败：{e}")
                st.stop()
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

        # 记录消息数，避免追加旧消息导致重复
        prev_count = len(st.session_state.iv_msgs)

        with st.spinner(""):
            try:
                agent.answer(st.session_state.iv_thread, answer)
            except Exception as e:
                st.error(f"请求失败：{e}")
                st.stop()
            state = agent.get_state(st.session_state.iv_thread)

        if state and state.values:
            all_msgs = state.values.get("messages", [])
            # 只取本次 invoke 新增的 AI 消息（反馈 + 下一题）
            new_msgs = [m for m in all_msgs if hasattr(m, "content") and m.type == "ai"]
            # 从最新消息中取尚未加入 iv_msgs 的
            for m in new_msgs:
                content = str(m.content)
                # 去重检查：如果 iv_msgs 最后几条不包含此内容，才追加
                existing = {x["content"] for x in st.session_state.iv_msgs}
                if content not in existing:
                    st.session_state.iv_msgs.append({"role": "assistant", "content": content})

        st.rerun()

# --- Done ---
elif st.session_state.iv_phase == "done":
    st.success("面试完成")

    # 持久化：记录面试成绩到长期记忆
    if not st.session_state.get("iv_recorded"):
        try:
            from src.memory.history_store import record_session, complete_session
            from src.memory.proficiency_store import update_proficiency
            state = agent.get_state(st.session_state.iv_thread)
            if state and state.values:
                scores = state.values.get("scores", [])
                topic = state.values.get("topic", "综合")
                if scores:
                    avg = sum(s.get("overall", 0) for s in scores) / len(scores)
                    sid = record_session("interview", topic, state.values.get("difficulty", ""))
                    complete_session(sid, avg, {"scores": scores})
                    # 更新主题熟练度
                    if "Java" in topic:
                        update_proficiency("java", avg)
                    if "Agent" in topic:
                        update_proficiency("agent", avg)
                st.session_state.iv_recorded = True
        except Exception:
            pass  # 记忆记录失败不阻塞 UI
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
