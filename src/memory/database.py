"""数据库初始化与迁移 — SQLite3 长期记忆存储。"""

import sqlite3
import os
from pathlib import Path


DB_PATH: str = ""


def get_db_path() -> str:
    """获取数据库文件路径。"""
    from config.settings import settings
    return str(Path(settings.user_data_dir) / "app.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建目录和文件）。"""
    path = get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """初始化所有表（幂等 — 使用 CREATE TABLE IF NOT EXISTS）。"""
    conn = get_connection()
    cursor = conn.cursor()

    # 用户档案
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '学习者',
            experience_level TEXT NOT NULL DEFAULT 'beginner',
            interview_goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 会话历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_type TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT,
            score REAL,
            details TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            duration_seconds INTEGER
        )
    """)

    # 主题熟练度
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_proficiency (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL UNIQUE,
            proficiency_score REAL DEFAULT 0.0,
            total_sessions INTEGER DEFAULT 0,
            last_practiced_at TIMESTAMP,
            weak_concepts TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
