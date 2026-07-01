"""用户档案 CRUD。"""

from __future__ import annotations

from src.memory.database import get_connection


def get_or_create_user() -> dict:
    """获取用户档案（不存在则创建默认）。"""
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM user_profile LIMIT 1").fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO user_profile (name, experience_level) VALUES ('学习者', 'beginner')"
        )
        conn.commit()
        row = cursor.execute("SELECT * FROM user_profile LIMIT 1").fetchone()
    conn.close()
    return dict(row)


def update_user(name: str | None = None, experience_level: str | None = None,
                interview_goal: str | None = None) -> None:
    """更新用户档案字段。"""
    conn = get_connection()
    cursor = conn.cursor()
    updates: dict[str, str] = {}
    if name is not None:
        updates["name"] = name
    if experience_level is not None:
        updates["experience_level"] = experience_level
    if interview_goal is not None:
        updates["interview_goal"] = interview_goal
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        cursor.execute(
            f"UPDATE user_profile SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            list(updates.values()),
        )
        conn.commit()
    conn.close()
