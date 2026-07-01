"""知识测验 — Apple 极简风格。"""

import streamlit as st
from dotenv import load_dotenv; load_dotenv()

st.set_page_config(page_title="Quiz", page_icon="◈")
from src.utils.session import init_session_state
init_session_state()

st.html("""
<style>
#MainMenu, footer, .stDeployButton { display: none; }
h1 { font-size: 2rem !important; font-weight: 700 !important; color: #1D1D1F; }
.stButton > button {
    background: #0071E3; color: white; border: none; border-radius: 12px;
    padding: 0.6rem 1.5rem; font-weight: 500;
}
.stButton > button:hover { background: #0077ED; }
.stRadio label {
    background: #F5F5F7; border-radius: 10px; padding: 0.75rem 1rem;
    border: 1px solid #E8E8ED; cursor: pointer; margin-bottom: 0.25rem;
}
.stRadio label:hover { border-color: #0071E3; }
</style>
""")

st.title("Quiz")
st.html('<p style="color:#86868B;font-size:0.95rem;margin-bottom:1.5rem">AI 自动出题 · 即时反馈 · 成绩报告</p>')

# Agent
@st.cache_resource
def get_quiz_agent(provider: str, model: str):
    from src.utils.session import get_shared_llm
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.quiz_agent import QuizAgent
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""
    return QuizAgent(get_shared_llm(), cm.get_checkpointer(), ctx), cm

agent, cm = get_quiz_agent(
    st.session_state.get("current_provider", ""),
    st.session_state.get("current_model", ""),
)

for k in ["qz_phase", "qz_thread", "qz_msgs", "qz_cfg", "qz_choice"]:
    if k not in st.session_state:
        st.session_state[k] = "setup" if k == "qz_phase" else (None if k == "qz_thread" else [] if k == "qz_msgs" else {} if k == "qz_cfg" else None)

# --- Setup ---
if st.session_state.qz_phase == "setup":
    st.html('<div style="max-width:480px;margin:2rem auto">')

    topic = st.selectbox("主题", ["Java + Agent 综合", "Java 基础", "JVM", "并发编程", "Spring", "Agent 基础", "Agent 工具", "RAG", "多 Agent"])
    difficulty = st.selectbox("难度", ["初级", "中级", "高级"], index=1)
    count = st.selectbox("题数", [5, 10, 15], index=0)

    st.html('<div style="height:1rem"></div>')

    if st.button("开始测验", type="primary", use_container_width=True):
        with st.spinner("AI 出题中..."):
            tid = cm.new_thread_id()
            try:
                result = agent.start(tid, topic, difficulty, count)
            except Exception as e:
                st.error(f"请求失败：{e}")
                st.stop()
        state = agent.get_state(tid)
        qs = state.values.get("questions", []) if state and state.values else []
        st.session_state.qz_thread = tid
        st.session_state.qz_cfg = {"topic": topic, "difficulty": difficulty, "count": count}
        st.session_state.qz_msgs = []
        st.session_state.qz_phase = "answering"
        st.rerun()

    st.html('</div>')

# --- Answering ---
elif st.session_state.qz_phase == "answering":
    state = agent.get_state(st.session_state.qz_thread)
    if not state or not state.values:
        st.error("状态丢失")
        st.stop()

    v = state.values
    complete = v.get("quiz_complete", False)
    current = v.get("current_question_index", 0)
    total = v.get("total_questions", 0)
    scores = v.get("scores", [])
    questions = v.get("questions", [])

    if complete:
        st.session_state.qz_phase = "done"
        st.rerun()

    # 进度
    if total:
        correct = sum(scores)
        st.progress(current / total, text=f"进度 {current}/{total} · 正确 {correct}/{len(scores) if scores else 0}")

    # 显示上一题反馈
    for msg in st.session_state.qz_msgs:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 当前题目
    if current < total and current < len(questions):
        q = questions[current]
        st.html(f"""
        <div style="background:#F5F5F7;border-radius:14px;padding:1.5rem;margin:1rem 0">
            <p style="color:#86868B;font-size:0.85rem;margin-bottom:0.5rem">第 {current+1} 题 / {total}</p>
            <p style="font-size:1.1rem;font-weight:500;color:#1D1D1F;line-height:1.5">{q['question']}</p>
        </div>
        """)

        options = [opt.split(". ", 1)[-1] for opt in q["options"]]
        choice = st.radio("选择答案", options, index=None, key=f"q_{current}", label_visibility="collapsed")

        if choice and st.button("提交", type="primary", use_container_width=True):
            idx = options.index(choice)
            st.session_state.qz_msgs.append({"role": "user", "content": f"选择: {choice}"})

            with st.spinner(""):
                try:
                    agent.answer(st.session_state.qz_thread, idx)
                except Exception as e:
                    st.error(f"请求失败：{e}")
                    st.stop()

            state2 = agent.get_state(st.session_state.qz_thread)
            if state2 and state2.values:
                new_msgs = [m for m in state2.values.get("messages", [])[-3:]
                           if hasattr(m, "content") and m.type == "ai"]
                for m in new_msgs:
                    if m.content not in [x.get("content", "") for x in st.session_state.qz_msgs]:
                        st.session_state.qz_msgs.append({"role": "assistant", "content": str(m.content)})
                if state2.values.get("quiz_complete"):
                    st.session_state.qz_phase = "done"
            st.rerun()

# --- Done ---
elif st.session_state.qz_phase == "done":
    st.success("测验完成")

    # 持久化：记录测验成绩到长期记忆
    if not st.session_state.get("qz_recorded"):
        try:
            from src.memory.history_store import record_session, complete_session
            from src.memory.proficiency_store import update_proficiency
            state = agent.get_state(st.session_state.qz_thread)
            if state and state.values:
                scores = state.values.get("scores", [])
                topic = state.values.get("topic", "综合")
                total = state.values.get("total_questions", 5)
                correct = sum(scores)
                pct = correct / total * 100 if total else 0
                sid = record_session("quiz", topic, state.values.get("difficulty", ""))
                complete_session(sid, pct / 10, {"correct": correct, "total": total})
                if "Java" in topic:
                    update_proficiency("java", pct / 10)
                if "Agent" in topic:
                    update_proficiency("agent", pct / 10)
                st.session_state.qz_recorded = True
        except Exception:
            pass
    state = agent.get_state(st.session_state.qz_thread)
    if state and state.values:
        scores = state.values.get("scores", [])
        total = state.values.get("total_questions", 5)
        correct = sum(scores)
        pct = correct / total * 100 if total else 0
        st.metric("正确率", f"{correct}/{total} ({pct:.0f}%)")

    for msg in st.session_state.qz_msgs:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("再来一次", use_container_width=True):
            for k in ["qz_phase", "qz_thread", "qz_msgs", "qz_cfg"]:
                st.session_state[k] = "setup" if k == "qz_phase" else (None if k == "qz_thread" else [] if k == "qz_msgs" else {})
            st.rerun()
    with c2:
        if st.button("返回首页", use_container_width=True):
            st.switch_page("app.py")
