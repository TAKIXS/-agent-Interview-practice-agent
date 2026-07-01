"""主题熟练度追踪 — 指数加权移动平均更新。"""

from __future__ import annotations
import json
from datetime import datetime

from src.memory.database import get_connection


# 近期权重（最新表现 vs 历史趋势）
ALPHA = 0.3  # 新成绩权重
BETA = 0.7   # 旧熟练度权重（指数衰减）


def get_all_proficiencies() -> list[dict]:
    """获取所有主题的熟练度。"""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM topic_proficiency ORDER BY proficiency_score ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_proficiency(topic: str, score: float, weak_concepts: list[str] | None = None) -> dict:
    """更新单主题熟练度（指数加权移动平均）。

    new_score = old_score * BETA + latest_score * ALPHA
    """
    conn = get_connection()
    cursor = conn.cursor()

    existing = cursor.execute(
        "SELECT * FROM topic_proficiency WHERE topic = ?", (topic,)
    ).fetchone()

    if existing:
        old_score = existing["proficiency_score"]
        new_score = old_score * BETA + score * ALPHA
        cursor.execute(
            """UPDATE topic_proficiency
               SET proficiency_score = ?, total_sessions = total_sessions + 1,
                   last_practiced_at = CURRENT_TIMESTAMP,
                   weak_concepts = ?, updated_at = CURRENT_TIMESTAMP
               WHERE topic = ?""",
            (new_score, json.dumps(weak_concepts or [], ensure_ascii=False), topic),
        )
    else:
        new_score = score
        cursor.execute(
            """INSERT INTO topic_proficiency (topic, proficiency_score, total_sessions, weak_concepts)
               VALUES (?, ?, 1, ?)""",
            (topic, new_score, json.dumps(weak_concepts or [], ensure_ascii=False)),
        )

    conn.commit()
    conn.close()
    return {"topic": topic, "proficiency_score": new_score}


def get_weak_topics(threshold: float = 6.0) -> list[dict]:
    """获取薄弱主题（分数低于阈值）。"""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM topic_proficiency WHERE proficiency_score < ? ORDER BY proficiency_score ASC",
        (threshold,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
