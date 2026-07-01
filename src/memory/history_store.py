"""会话历史记录 — 面试、测验、代码练习的持久化存储。"""

from __future__ import annotations
import json
from datetime import datetime

from src.memory.database import get_connection


def record_session(
    session_type: str,
    topic: str | None = None,
    difficulty: str | None = None,
    score: float | None = None,
    details: dict | None = None,
) -> int:
    """记录一次会话（开始时调用）。返回 session_id。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO session_history (session_type, topic, difficulty, score, details) VALUES (?, ?, ?, ?, ?)",
        (session_type, topic, difficulty, score, json.dumps(details or {}, ensure_ascii=False)),
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def complete_session(session_id: int, score: float, details: dict | None = None) -> None:
    """标记会话完成，记录得分。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE session_history SET score = ?, details = ?, completed_at = CURRENT_TIMESTAMP, "
        "duration_seconds = (strftime('%s', 'now') - strftime('%s', started_at)) WHERE id = ?",
        (score, json.dumps(details or {}, ensure_ascii=False), session_id),
    )
    conn.commit()
    conn.close()


def get_recent_sessions(limit: int = 20, session_type: str | None = None) -> list[dict]:
    """获取最近的会话记录。"""
    conn = get_connection()
    cursor = conn.cursor()
    if session_type:
        rows = cursor.execute(
            "SELECT * FROM session_history WHERE session_type = ? ORDER BY started_at DESC LIMIT ?",
            (session_type, limit),
        ).fetchall()
    else:
        rows = cursor.execute(
            "SELECT * FROM session_history ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
