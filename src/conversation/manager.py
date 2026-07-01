"""多轮对话线程管理。

使用 LangGraph SqliteSaver 实现：
- 每个功能页面独立 thread_id
- 页面刷新后自动恢复上次对话
- 消息历史持久化到 SQLite
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


class ConversationManager:
    """管理各功能模块的对话线程。"""

    def __init__(self, db_path: str = "user_data/checkpoints.db") -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # SqliteSaver 需要一个 sqlite3 连接
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._saver = SqliteSaver(self._conn)
        self._saver.setup()

    def get_checkpointer(self):
        """返回 SqliteSaver 实例（用于 LangGraph compile 时传入）。"""
        return self._saver

    @staticmethod
    def new_thread_id() -> str:
        """生成新的对话线程 ID。"""
        return str(uuid.uuid4())

    @staticmethod
    def make_config(thread_id: str) -> dict:
        """构建 LangGraph config dict。"""
        return {"configurable": {"thread_id": thread_id}}

    def close(self) -> None:
        """关闭数据库连接。"""
        self._conn.close()


# 全局单例
conversation_manager = ConversationManager()
