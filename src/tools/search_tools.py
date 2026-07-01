"""知识库搜索工具 — LangChain BaseTool 封装。"""

from __future__ import annotations

from langchain_core.tools import tool

# 全局 retriever 引用（由 QA Agent 初始化时设置）
_retriever = None


def set_retriever(retriever) -> None:
    """设置全局检索器。"""
    global _retriever
    _retriever = retriever


@tool
def search_knowledge_base(query: str) -> str:
    """搜索内部知识库，获取 Java 和 LangChain Agent 相关的技术文档。

    当用户询问 Java 技术问题（如 HashMap、JVM、线程池、Spring）或
    LangChain Agent 问题（如 Agent 类型、工具使用、RAG、多 Agent）时，
    使用此工具检索相关文档。

    Args:
        query: 搜索查询，应该是一段描述性文本
    """
    if _retriever is None:
        return "知识库尚未初始化，请先完成索引。"

    docs = _retriever.retrieve(query, k=5)
    if not docs:
        return "未找到相关文档。"

    results = []
    for i, doc in enumerate(docs, 1):
        category = doc.metadata.get("category", "未知")
        filename = doc.metadata.get("filename", "")
        results.append(f"[来源{i}: {category}/{filename}]\n{doc.page_content}")

    return "\n\n---\n\n".join(results)


@tool
def search_by_category(query: str, category: str) -> str:
    """在指定分类中搜索知识库文档。

    可用于精确搜索某个领域的知识。
    分类可选: java_core, java_jvm, java_concurrency, java_spring,
    java_architecture, agent_fundamentals, agent_tools, agent_rag,
    agent_multi, agent_production

    Args:
        query: 搜索查询
        category: 分类名称
    """
    if _retriever is None:
        return "知识库尚未初始化。"

    docs = _retriever.retrieve(query, k=5, category=category)
    if not docs:
        return f"在 {category} 分类中未找到相关文档。"

    results = []
    for i, doc in enumerate(docs, 1):
        filename = doc.metadata.get("filename", "")
        results.append(f"[{i}: {filename}]\n{doc.page_content}")

    return "\n\n---\n\n".join(results)
