"""ConversationSummaryBuffer — 长对话自动摘要压缩。

策略：
- 保留最近 N 轮完整对话（默认 10 轮 = 20 条消息）
- 超出部分用 LLM 压缩为一段 200 字摘要
- 摘要作为 system 消息插入对话开头，保持 token 在安全范围内
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


class ConversationSummarizer:
    """管理对话历史的自动摘要。"""

    SUMMARIZE_PROMPT = """请用中文将以下对话历史压缩为一段不超过 200 字的摘要，保留关键信息：

{history}

摘要："""

    def __init__(
        self,
        llm: BaseChatModel,
        max_recent_rounds: int = 10,
        summary_max_chars: int = 200,
    ) -> None:
        self._llm = llm
        self._max_recent_rounds = max_recent_rounds
        self._summary_max_chars = summary_max_chars

    def manage_context(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """管理对话上下文：返回压缩后的消息列表。

        如果消息数 <= max_recent_rounds * 2，直接返回。
        否则，将旧消息压缩为摘要，保留最近的消息。
        """
        threshold = self._max_recent_rounds * 2  # 每轮 user + assistant

        if len(messages) <= threshold:
            return messages

        # 分割：旧消息 → 摘要，新消息 → 保留
        old_messages = messages[:-threshold]
        recent_messages = messages[-threshold:]

        summary = self._summarize(old_messages)

        # 构建新消息列表：summary system message + 最近消息
        result: list[BaseMessage] = [
            SystemMessage(content=f"[对话历史摘要] {summary}")
        ]
        result.extend(recent_messages)
        return result

    def _summarize(self, messages: list[BaseMessage]) -> str:
        """调用 LLM 将消息列表压缩为摘要文本。"""
        history_text = "\n".join(
            f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {m.content[:300]}"
            for m in messages
        )
        prompt = self.SUMMARIZE_PROMPT.format(history=history_text)

        try:
            response = self._llm.invoke(prompt)
            return str(response.content)[: self._summary_max_chars]
        except Exception:
            # LLM 不可用时，简单截断
            return f"之前的对话（{len(messages)} 条消息）"
