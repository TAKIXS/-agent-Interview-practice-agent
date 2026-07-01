"""构建注入 Agent 的个性化记忆上下文。

从数据库查询用户档案和熟练度，生成一段注入 system prompt 的文本。
"""

from __future__ import annotations


def build_memory_context() -> str:
    """构建注入 Agent system prompt 的个性化上下文。

    Returns:
        一段描述用户背景和熟练度的文本，或空字符串（首次使用时）。
    """
    from src.memory.user_store import get_or_create_user
    from src.memory.proficiency_store import get_all_proficiencies, get_weak_topics

    try:
        user = get_or_create_user()
        proficiencies = get_all_proficiencies()
    except Exception:
        return ""  # 数据库未初始化时静默返回

    parts: list[str] = []

    # 用户背景
    level_labels = {"beginner": "初级", "intermediate": "中级", "advanced": "高级"}
    level = level_labels.get(user.get("experience_level", "beginner"), "初级")
    parts.append(f"- 学习阶段：{level}")
    if user.get("interview_goal"):
        parts.append(f"- 面试目标：{user['interview_goal']}")

    # 熟练度概况
    if proficiencies:
        strong = [p for p in proficiencies if p["proficiency_score"] >= 7.5]
        weak = [p for p in proficiencies if p["proficiency_score"] < 6.0]

        if strong:
            topics_str = ", ".join(
                f"{p['topic']}({p['proficiency_score']:.1f})" for p in strong
            )
            parts.append(f"- 强项：{topics_str}")

        if weak:
            topics_str = ", ".join(
                f"{p['topic']}({p['proficiency_score']:.1f})" for p in weak
            )
            parts.append(f"- 弱项：{topics_str}")
            parts.append("- 请在回答中重点关注弱项相关的概念，讲解更详细一些")

    if not parts:
        return ""

    return "## 学习者档案\n" + "\n".join(parts)
