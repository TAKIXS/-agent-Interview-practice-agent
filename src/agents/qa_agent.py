"""QAAgent — 基于 LangGraph + RAG 的知识问答 Agent。

图结构（3 节点）：
  [manage_context] → [retrieve] → [generate] → END
       ↑                                |
       └── 强制重新检索时走此路 ──────────┘

功能：
- 多轮对话：保留历史上下文，自动摘要长对话
- RAG 检索：从知识库检索相关文档
- 流式生成：逐 token 输出到 Streamlit
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.state.schemas import AgentState
from src.conversation.summarizer import ConversationSummarizer
from src.conversation.manager import ConversationManager
from src.tools.search_tools import set_retriever

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

QA_SYSTEM_PROMPT = """你是一位专业的 AI 面试辅导专家，精通 Java 后端开发和 LangChain Agent 技术。

## 你的领域
- **Java**: 集合框架、JVM、并发编程、Spring 框架、微服务架构
- **LangChain Agent**: Agent 类型、工具集成、RAG、多 Agent 系统、生产部署

## 回答规则
1. 优先使用「检索到的知识库文档」来回答问题
2. 回答中引用文档来源（如 `[java_core/01_java_basics.md]`）
3. 知识库未覆盖的内容，可基于你的专业知识补充回答，并标注「基于通用知识」
4. 提供具体的代码示例
5. 使用中文回答，技术术语保持英文

## 学习者档案
{memory_context}

## 检索到的知识库文档
{retrieved_docs}
"""


# ---------------------------------------------------------------------------
# QAAgent
# ---------------------------------------------------------------------------

class QAAgent:
    """知识问答 Agent — LangGraph 驱动的多轮 RAG 对话。"""

    def __init__(
        self,
        llm: BaseChatModel,
        retriever,
        checkpointer,
        memory_context: str = "",
    ) -> None:
        self._llm = llm
        self._retriever = retriever
        self._summarizer = ConversationSummarizer(llm, max_recent_rounds=10)
        self._memory_context = memory_context

        # 将 retriever 注册到 search_tools 中
        set_retriever(retriever)

        # 构建并编译图
        self._graph: CompiledStateGraph = self._build_graph()
        # 编译时注入 checkpointer 以支持多轮对话持久化
        self._graph_with_memory = self._graph.compile(checkpointer=checkpointer)

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def invoke(self, question: str, thread_id: str) -> dict[str, Any]:
        """同步调用（非流式）。"""
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph_with_memory.invoke(
            {"messages": [HumanMessage(content=question)]},
            config=config,
        )

    async def astream(self, question: str, thread_id: str):
        """异步流式调用 — 逐 token 输出生成内容。

        使用方式：
            async for event in agent.astream("什么是 HashMap?", thread_id):
                if event["event"] == "on_chat_model_stream":
                    yield event["data"]["chunk"].content
        """
        config = {"configurable": {"thread_id": thread_id}}
        async for event in self._graph_with_memory.astream_events(
            {"messages": [HumanMessage(content=question)]},
            config=config,
            version="v2",
        ):
            yield event

    def new_thread(self) -> str:
        """创建新的对话线程。"""
        from src.conversation.manager import ConversationManager
        return ConversationManager.new_thread_id()

    # ------------------------------------------------------------------
    # 图构建
    # ------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("manage_context", self._manage_context_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("generate", self._generate_node)

        graph.set_entry_point("manage_context")
        graph.add_edge("manage_context", "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)

        return graph

    # ------------------------------------------------------------------
    # 节点实现
    # ------------------------------------------------------------------

    def _manage_context_node(self, state: AgentState) -> dict:
        """管理对话上下文：压缩长历史 + 提取最新问题。"""
        messages = state["messages"]

        # 摘要压缩
        compressed = self._summarizer.manage_context(messages)

        # 最后一条用户消息作为查询
        last_query = ""
        for m in reversed(compressed):
            if isinstance(m, HumanMessage):
                last_query = str(m.content)
                break

        return {
            "messages": compressed,
            "metadata": {"last_query": last_query},
        }

    def _retrieve_node(self, state: AgentState) -> dict:
        """检索知识库文档。"""
        last_query = state.get("metadata", {}).get("last_query", "")

        try:
            docs = self._retriever.retrieve(last_query, k=5)
        except Exception:
            docs = []

        # 格式化检索结果
        if docs:
            retrieved_text = "\n\n---\n\n".join(
                f"[来源{i}: {d.metadata.get('category', '?')}/{d.metadata.get('filename', '?')}]\n{d.page_content}"
                for i, d in enumerate(docs, 1)
            )
        else:
            retrieved_text = "（未检索到相关文档，请基于通用知识回答）"

        return {
            "metadata": {
                **state.get("metadata", {}),
                "retrieved_docs": retrieved_text,
            },
        }

    def _generate_node(self, state: AgentState) -> dict:
        """生成最终回答。"""
        messages = state["messages"]
        retrieved_docs = state.get("metadata", {}).get("retrieved_docs", "")
        memory_ctx = self._memory_context

        # 构建 prompt
        system_content = QA_SYSTEM_PROMPT.format(
            memory_context=memory_ctx if memory_ctx else "（新用户，尚无学习记录）",
            retrieved_docs=retrieved_docs,
        )

        # 将 system message 放在消息列表最前面
        full_messages: list[BaseMessage] = [SystemMessage(content=system_content)]
        full_messages.extend(messages)

        response = self._llm.invoke(full_messages)
        return {"messages": [response]}
