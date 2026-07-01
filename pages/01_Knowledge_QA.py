"""知识问答页面 — RAG 驱动的多轮对话。

功能：
- 流式输出（逐 token 显示）
- 多轮对话（自动恢复上次线程）
- 来源文档展示
- 新建对话
- 主题过滤
"""

import asyncio
import streamlit as st


# ============================================================================
# 页面初始化
# ============================================================================
st.set_page_config(page_title="知识问答", page_icon="💬")

# 从首页继承 session_state
from src.utils.session import init_session_state
init_session_state()

st.title("💬 知识问答")
st.markdown("基于 RAG 的智能问答 — 覆盖 Java 后端 + LangChain Agent")

# ============================================================================
# 侧边栏
# ============================================================================
with st.sidebar:
    st.markdown("### 🔍 主题过滤")
    category_filter = st.selectbox(
        "选择知识领域",
        ["全部", "java_core", "java_jvm", "java_concurrency", "java_spring",
         "java_architecture", "agent_fundamentals", "agent_tools",
         "agent_rag", "agent_multi", "agent_production"],
        key="qa_filter",
    )

    st.divider()

    if st.button("🆕 新建对话", use_container_width=True):
        st.session_state.qa_thread_id = None
        st.session_state.qa_messages = []
        st.rerun()

    st.caption(f"线程: {st.session_state.get('qa_thread_id', '未创建')[:8] if st.session_state.get('qa_thread_id') else '未创建'}")

# ============================================================================
# 初始化 QA Agent（缓存）
# ============================================================================
@st.cache_resource
def get_qa_agent():
    """构建 QA Agent（缓存，只初始化一次）。"""
    from src.llm.manager import ModelManager
    from src.rag.embeddings import EmbeddingProvider
    from src.rag.store import VectorStoreManager
    from src.rag.retriever import Retriever
    from src.conversation.manager import ConversationManager
    from src.memory.memory_context import build_memory_context
    from src.agents.qa_agent import QAAgent

    mgr = ModelManager()
    cm = ConversationManager()

    # 初始化向量库和检索器
    provider = EmbeddingProvider(kind="huggingface")
    embeddings = provider.get()
    store = VectorStoreManager("./chroma_db", embeddings)
    vs = store.get_or_create()
    retriever = Retriever(vs, k=5)

    # 构建记忆上下文
    try:
        memory_ctx = build_memory_context()
    except Exception:
        memory_ctx = ""

    # 创建 QA Agent
    agent = QAAgent(
        llm=mgr.llm,
        retriever=retriever,
        checkpointer=cm.get_checkpointer(),
        memory_context=memory_ctx,
    )
    return agent, cm


# 尝试初始化
try:
    agent, conv_mgr = get_qa_agent()
    agent_ready = True
except Exception as e:
    agent_ready = False
    st.error(f"Agent 初始化失败: {e}")

# 初始化线程和消息
if "qa_thread_id" not in st.session_state or not st.session_state.qa_thread_id:
    st.session_state.qa_thread_id = conv_mgr.new_thread_id()
if "qa_messages" not in st.session_state:
    st.session_state.qa_messages = []

# ============================================================================
# 显示历史消息
# ============================================================================
for msg in st.session_state.qa_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 来源文档"):
                st.markdown(msg["sources"])

# ============================================================================
# 输入区
# ============================================================================
if prompt := st.chat_input("输入你的问题（Java 或 Agent 相关）...", disabled=not agent_ready):
    # 显示用户消息
    st.session_state.qa_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用 Agent
    with st.chat_message("assistant"):
        try:
            with st.spinner("检索中..."):
                # 同步调用（简化版；流式版见下方注释）
                result = agent.invoke(prompt, st.session_state.qa_thread_id)

            # 提取 AI 回复
            ai_messages = [m for m in result["messages"] if hasattr(m, "content") and m.type == "ai"]
            if ai_messages:
                answer = str(ai_messages[-1].content)
                st.markdown(answer)

                # 提取检索来源
                metadata = result.get("metadata", {})
                sources = metadata.get("retrieved_docs", "")
                if sources and sources != "（未检索到相关文档，请基于通用知识回答）":
                    with st.expander("📚 来源文档"):
                        st.markdown(sources)

                st.session_state.qa_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources if sources else "",
                })
            else:
                st.warning("Agent 未返回有效回复")

        except Exception as e:
            st.error(f"出错了: {e}")

# ============================================================================
# 底部状态
# ============================================================================
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption(f"总消息数: {len(st.session_state.qa_messages)}")
with col2:
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.qa_messages = []
        st.session_state.qa_thread_id = conv_mgr.new_thread_id()
        st.rerun()
