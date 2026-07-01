"""BaseAgent — 所有功能 Agent 的抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel


class BaseAgent(ABC):
    """Agent 基类，定义统一的 invoke / astream 接口。"""

    def __init__(self, llm: BaseChatModel, memory_context: str = "") -> None:
        self.llm = llm
        self.memory_context = memory_context

    @abstractmethod
    def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """同步调用 Agent。"""
        ...

    async def astream(self, input_data: dict[str, Any]):
        """异步流式调用 Agent。子类可按需覆写。"""
        raise NotImplementedError
