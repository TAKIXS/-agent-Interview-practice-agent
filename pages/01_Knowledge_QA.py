"""知识问答 — Apple 极简风格。"""

import streamlit as st
from dotenv import load_dotenv; load_dotenv()

st.set_page_config(page_title="Q&A", page_icon="◈")
from src.utils.session import init_session_state
init_session_state()

# 注入 CSS
st.html("""
<style>
#MainMenu, footer, .stDeployButton { display: none; }
h1 { font-size: 2rem !important; font-weight: 700 !important; color: #1D1D1F; }
.chat-container { max-width: 800px; margin: 0 auto; }
.stChatMessage { background: transparent !important; padding: 1rem 0; }
.stChatMessage [data-testid="stChatMessageContent"] {
    background: #F5F5F7;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    max-width: 85%;
}
.stChatMessage[data-testid="stChatMessage-user"] [data-testid="stChatMessageContent"] {
    background: #0071E3;
    color: white;
    margin-left: auto;
}
.stChatInput > div {
    border-radius: 12px;
    border: 1px solid #D1D1D6;
}
</style>
""")

st.title("Q&A")
st.html('<p style="color:#86868B;font-size:0.95rem;margin-bottom:1.5rem">基于知识库的智能问答 · Java 后端 + LangChain Agent</p>')

# Agent
@st.cache_resource
def get_qa():
    from src.llm.manager import ModelManager
    from src.rag.embeddings import EmbeddingProvider
    from src.rag.store import VectorStoreManager
    from src.rag.retriever import Retriever
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.qa_agent import QAAgent

    provider = EmbeddingProvider(kind="huggingface")
    store = VectorStoreManager("./chroma_db", provider.get())
    vs = store.get_or_create()
    retriever = Retriever(vs, k=5)
    cm = ConversationManager()
    try:
        ctx = build_memory_context()
    except Exception:
        ctx = ""
    agent = QAAgent(ModelManager().llm, retriever, cm.get_checkpointer(), ctx)
    return agent, cm

agent, cm = get_qa()

if "qa_thread" not in st.session_state or not st.session_state.qa_thread:
    st.session_state.qa_thread = cm.new_thread_id()
if "qa_msgs" not in st.session_state:
    st.session_state.qa_msgs = []

# 显示消息
st.html('<div class="chat-container">')
for msg in st.session_state.qa_msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("来源"):
                st.caption(msg["sources"][:500])
st.html('</div>')

# 输入
if prompt := st.chat_input("提出问题..."):
    st.session_state.qa_msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            result = agent.invoke(prompt, st.session_state.qa_thread)
        answers = [m for m in result.get("messages", []) if hasattr(m, "content") and m.type == "ai"]
        if answers:
            answer = str(answers[-1].content)
            st.markdown(answer)
            sources = result.get("metadata", {}).get("retrieved_docs", "")
            st.session_state.qa_msgs.append({"role": "assistant", "content": answer, "sources": sources})

# 侧边栏
with st.sidebar:
    st.markdown("**Q&A**")
    if st.button("新建对话", use_container_width=True):
        st.session_state.qa_thread = cm.new_thread_id()
        st.session_state.qa_msgs = []
        st.rerun()
    st.caption(f"消息: {len(st.session_state.qa_msgs)}")
    if st.button("清空", use_container_width=True):
        st.session_state.qa_msgs = []
        st.rerun()
