"""学习进度 — Apple 极简风格。"""

import streamlit as st
from dotenv import load_dotenv; load_dotenv()

st.set_page_config(page_title="进度", page_icon="◈")
from src.utils.session import init_session_state
init_session_state()

st.html("""
<style>
#MainMenu, footer, .stDeployButton { display: none; }
h1 { font-size: 2rem !important; font-weight: 700 !important; color: #1D1D1F; }
.stButton > button { background: #F5F5F7; color: #0071E3; border: none; border-radius: 980px; }
</style>
""")

st.title("进度")
st.html('<p style="color:#86868B;font-size:0.95rem;margin-bottom:1.5rem">学习轨迹与成长记录</p>')

try:
    from src.memory.history_store import get_recent_sessions
    from src.memory.proficiency_store import get_all_proficiencies, get_weak_topics
    from src.memory.database import init_db
    init_db()

    sessions = get_recent_sessions(50)
    profs = get_all_proficiencies()
    weak = get_weak_topics()

    # 统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("学习会话", str(len(sessions)))
    with col2:
        quiz_sessions = [s for s in sessions if s.get("session_type") == "quiz"]
        interview_sessions = [s for s in sessions if s.get("session_type") == "interview"]
        st.metric("面试", str(len(interview_sessions)))
    with col3:
        st.metric("测验", str(len(quiz_sessions)))

    # 熟练度
    if profs:
        st.divider()
        st.markdown("### 主题熟练度")
        for p in profs:
            score = p.get("proficiency_score", 0)
            topic = p.get("topic", "?")
            st.progress(min(score / 10, 1.0), text=f"{topic}: {score:.1f}/10")

    # 弱点提示
    if weak:
        st.divider()
        st.markdown("### 需要加强")
        for w in weak:
            st.markdown(f"- **{w.get('topic','?')}**: {w.get('proficiency_score',0):.1f}/10")

    # 最近活动
    if sessions:
        st.divider()
        st.markdown("### 最近活动")
        for s in sessions[:10]:
            stype = {"interview": "面试", "quiz": "测验", "qa": "问答"}.get(s.get("session_type", ""), s.get("session_type", ""))
            topic = s.get("topic", "")
            score = s.get("score", 0)
            date = str(s.get("started_at", ""))[:10] if s.get("started_at") else ""
            st.markdown(f"- {date} {stype} {topic}: {score:.1f}/10")

    if not sessions and not profs:
        st.info("还没有学习记录。完成一次面试或测验后这里会有数据。")

except Exception as e:
    st.warning(f"数据加载失败: {e}")
