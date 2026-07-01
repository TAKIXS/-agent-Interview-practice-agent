"""知识问答 — Apple 极简风格。"""

import streamlit as st
from dotenv import load_dotenv; load_dotenv()

st.set_page_config(page_title="Q&A", page_icon="◈")
from src.utils.session import init_session_state
init_session_state()

# CSS
st.html("""
<style>
#MainMenu, footer, .stDeployButton { display: none; }
h1 { font-size: 2rem !important; font-weight: 700 !important; color: #1D1D1F; }
.stChatMessage { background: transparent !important; padding: 1rem 0; }
.stChatMessage [data-testid="stChatMessageContent"] {
    background: #F5F5F7; border-radius: 14px; padding: 1rem 1.25rem; max-width: 85%;
}
.stChatMessage[data-testid="stChatMessage-user"] [data-testid="stChatMessageContent"] {
    background: #0071E3; color: white; margin-left: auto;
}
.stChatInput > div { border-radius: 12px; border: 1px solid #D1D1D6; }
</style>
""")

st.title("Q&A")
st.html('<p style="color:#86868B;font-size:0.95rem;margin-bottom:1.5rem">基于知识库的智能问答 · Java 后端 + LangChain Agent</p>')

# RAG + Agent 懒加载（首次提问时才初始化，页面秒开）
@st.cache_resource(show_spinner="加载知识库...")
def get_qa_agent(provider: str, model: str):
    from src.rag.embeddings import EmbeddingProvider
    from src.rag.store import VectorStoreManager
    from src.rag.retriever import Retriever
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.utils.session import get_shared_llm
    from src.agents.qa_agent import QAAgent

    provider_obj = EmbeddingProvider(kind="huggingface")
    store = VectorStoreManager("./chroma_db", provider_obj.get())
    vs = store.get_or_create()
    retriever = Retriever(vs, k=5)
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""
    return QAAgent(get_shared_llm(), retriever, cm.get_checkpointer(), ctx), cm

# 延迟加载：只在需要时创建 agent
_agent = None
_cm = None

def ensure_agent():
    global _agent, _cm
    if _agent is None:
        _agent, _cm = get_qa_agent(
            st.session_state.get("current_provider", ""),
            st.session_state.get("current_model", ""),
        )
    return _agent, _cm

# 初始化（不触发模型加载）
if "qa_thread" not in st.session_state:
    st.session_state.qa_thread = None
if "qa_msgs" not in st.session_state:
    st.session_state.qa_msgs = []

# 显示历史消息 — 直接循环，不用 HTML 包裹
for msg in st.session_state.qa_msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("来源"):
                st.caption(msg["sources"][:500])

# 输入
if prompt := st.chat_input("提出问题..."):
    # 用户消息
    st.session_state.qa_msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 回答（触发懒加载）
    with st.chat_message("assistant"):
        try:
            agent, cm = ensure_agent()
            if st.session_state.qa_thread is None:
                st.session_state.qa_thread = cm.new_thread_id()
            with st.spinner(""):
                result = agent.invoke(prompt, st.session_state.qa_thread)
            answers = [m for m in result.get("messages", []) if hasattr(m, "content") and m.type == "ai"]
            if answers:
                answer = str(answers[-1].content)
                st.markdown(answer)
                sources = result.get("metadata", {}).get("retrieved_docs", "")
                st.session_state.qa_msgs.append({"role": "assistant", "content": answer, "sources": sources})
        except Exception as e:
            st.error(f"请求失败：{e}")
            st.session_state.qa_msgs.append({"role": "assistant", "content": "抱歉，请求出错了。请稍后重试。"})
    st.rerun()

# 侧边栏
with st.sidebar:
    st.markdown("**Q&A**")
    st.caption(f"消息: {len(st.session_state.qa_msgs)}")
    if st.button("新建对话", use_container_width=True):
        agent, cm = ensure_agent()
        st.session_state.qa_thread = cm.new_thread_id()
        st.session_state.qa_msgs = []
        st.rerun()
