"""InterviewAgent — 模拟面试 Agent。"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from src.graphs.interview_graph import InterviewGraph


class InterviewAgent:
    """模拟面试 Agent。"""

    def __init__(self, llm: BaseChatModel, checkpointer, memory_context: str = "") -> None:
        self._graph = InterviewGraph(llm, checkpointer, memory_context)

    def start(self, thread_id: str, topic: str, difficulty: str, total: int) -> dict:
        """开始面试。"""
        return self._graph.start(thread_id, topic, difficulty, total)

    def answer(self, thread_id: str, user_answer: str) -> dict:
        """提交回答。"""
        return self._graph.answer(thread_id, user_answer)

    def get_state(self, thread_id: str):
        """获取状态。"""
        return self._graph.get_state(thread_id)
