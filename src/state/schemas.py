"""LangGraph 状态 Schema — TypedDict 定义。

各功能 Graph 共享的状态结构。
"""

from typing import Annotated, Any
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """通用 Agent 状态 — 用于 QA、路由等简单 Graph。"""
    messages: Annotated[list[BaseMessage], add_messages]
    memory_context: str
    metadata: dict[str, Any]


class InterviewState(TypedDict):
    """模拟面试状态。"""
    messages: Annotated[list[BaseMessage], add_messages]
    topic: str
    difficulty: str
    total_questions: int
    current_question_index: int
    questions_asked: list[str]
    user_answers: list[str]
    scores: list[dict[str, Any]]
    interview_complete: bool


class QuizState(TypedDict):
    """知识测验状态。"""
    messages: Annotated[list[BaseMessage], add_messages]
    topic: str
    difficulty: str
    total_questions: int
    current_question_index: int
    questions: list[dict[str, Any]]
    answers: list[str]
    scores: list[int]
    quiz_complete: bool


class CodeState(TypedDict):
    """代码实战状态。"""
    messages: Annotated[list[BaseMessage], add_messages]
    exercise_id: str
    user_code: str
    execution_output: str
    evaluation: dict[str, Any] | None
