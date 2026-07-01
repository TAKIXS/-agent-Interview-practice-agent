"""知识库搜索 — retriever 全局引用（由 QA Agent 设置）。"""

_retriever = None


def set_retriever(retriever) -> None:
    """设置全局检索器（QA Agent 初始化时调用）。"""
    global _retriever
    _retriever = retriever
