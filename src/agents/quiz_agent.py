"""QuizAgent — 知识测验 Agent。"""

from __future__ import annotations
from langchain_core.language_models import BaseChatModel
from src.graphs.quiz_graph import QuizGraph


class QuizAgent:
    """AI 出题 + 逐题作答 + 成绩报告。"""

    def __init__(self, llm: BaseChatModel, checkpointer, memory_context: str = "") -> None:
        self._graph = QuizGraph(llm, checkpointer, memory_context)

    def start(self, thread_id: str, topic: str, difficulty: str, count: int) -> dict:
        return self._graph.start(thread_id, topic, difficulty, count)

    def answer(self, thread_id: str, selected_index: int) -> dict:
        return self._graph.answer(thread_id, selected_index)

    def get_state(self, thread_id: str):
        return self._graph.get_state(thread_id)
