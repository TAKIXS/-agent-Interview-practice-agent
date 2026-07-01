"""QuizGraph — 知识测验 LangGraph 状态机。

流程：
  首次 invoke:  setup -> generate_questions -> ask_first -> END
  答题 invoke:  grade -> conditional ->
                    ask_next -> END (还有题)
                    final_report -> END (结束)
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.state.schemas import QuizState

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

GENERATE_QUESTIONS_PROMPT = """你是一位出题专家。请生成 {count} 道选择题。

## 主题：{topic}
## 难度：{difficulty}

## 要求
1. 每题 4 个选项（A/B/C/D），只有一个正确答案
2. 题目考察理解能力，不是死记硬背
3. 使用场景化出题：给出一个具体场景，问应该怎么处理
4. 每个选项有迷惑性
5. 正确答案附带解析
6. 输出纯 JSON 数组格式

## JSON 格式
```json
[
  {{
    "id": 1,
    "question": "题目文本",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "correct": 0,
    "explanation": "正确答案解析",
    "topic": "分类标签"
  }}
]
```

只输出 JSON 数组，不要其他内容。"""

# ---------------------------------------------------------------------------
# 主类
# ---------------------------------------------------------------------------

class QuizGraph:
    """知识测验图。"""

    def __init__(self, llm: BaseChatModel, checkpointer, memory_context: str = "") -> None:
        self._llm = llm
        self._memory = memory_context
        self._graph = self._build().compile(checkpointer=checkpointer)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def start(self, thread_id: str, topic: str, difficulty: str, count: int) -> dict:
        cfg = json.dumps({"topic": topic, "difficulty": difficulty, "total_questions": count}, ensure_ascii=False)
        return self._graph.invoke(
            {"messages": [HumanMessage(content=cfg)]},
            {"configurable": {"thread_id": thread_id}},
        )

    def answer(self, thread_id: str, selected_index: int) -> dict:
        return self._graph.invoke(
            {"messages": [HumanMessage(content=str(selected_index))]},
            {"configurable": {"thread_id": thread_id}},
        )

    def get_state(self, thread_id: str):
        return self._graph.get_state({"configurable": {"thread_id": thread_id}})

    # ------------------------------------------------------------------
    # 图构建
    # ------------------------------------------------------------------

    def _build(self) -> StateGraph:
        g = StateGraph(QuizState)

        g.add_node("setup", self._setup)
        g.add_node("generate", self._generate)
        g.add_node("ask_question", self._ask_question)
        g.add_node("grade", self._grade)
        g.add_node("final_report", self._final_report)
        g.add_node("router", lambda s: {})

        g.set_entry_point("router")
        g.add_conditional_edges("router", self._route, {
            "setup": "setup", "grade": "grade", "end": END,
        })

        g.add_edge("setup", "generate")
        g.add_edge("generate", "ask_question")
        g.add_edge("ask_question", END)

        g.add_conditional_edges("grade", self._after_grade, {
            "ask": "ask_question", "final": "final_report", "end": END,
        })
        g.add_edge("final_report", END)

        return g

    # ------------------------------------------------------------------
    # 路由
    # ------------------------------------------------------------------

    def _route(self, state: QuizState) -> Literal["setup", "grade", "end"]:
        if state.get("quiz_complete"):
            return "end"
        if state.get("total_questions", 0) == 0:
            return "setup"
        # 检查是否有待评分的用户回答（非 JSON 的 HumanMessage）
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                txt = str(m.content).strip()
                if txt.isdigit():
                    return "grade"  # 用户提交了选项编号
                try:
                    json.loads(txt)
                    return "setup"  # 新配置
                except (json.JSONDecodeError, ValueError):
                    return "grade"
        return "end"

    def _after_grade(self, state: QuizState) -> Literal["ask", "final", "end"]:
        total = state.get("total_questions", 0)
        current = state.get("current_question_index", 0)
        if state.get("quiz_complete"):
            return "end"
        if current >= total:
            return "final"
        return "ask"

    # ------------------------------------------------------------------
    # 节点
    # ------------------------------------------------------------------

    def _setup(self, state: QuizState) -> dict:
        msgs = state["messages"]
        for m in reversed(msgs):
            if isinstance(m, HumanMessage):
                try:
                    cfg = json.loads(str(m.content))
                    return {
                        "topic": cfg["topic"], "difficulty": cfg["difficulty"],
                        "total_questions": cfg["total_questions"],
                        "current_question_index": 0,
                        "questions": [], "answers": [], "scores": [],
                        "quiz_complete": False,
                    }
                except json.JSONDecodeError:
                    pass
        return {"topic": "综合", "difficulty": "中级", "total_questions": 5,
                "current_question_index": 0, "questions": [], "answers": [],
                "scores": [], "quiz_complete": False}

    def _generate(self, state: QuizState) -> dict:
        prompt = GENERATE_QUESTIONS_PROMPT.format(
            count=state["total_questions"], topic=state["topic"], difficulty=state["difficulty"],
        )
        resp = self._llm.invoke(prompt)
        text = str(resp.content)

        # 提取 JSON
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            questions = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            # 回退：生成简单题目
            questions = [{
                "id": i+1, "question": f"第{i+1}题", "options": ["A","B","C","D"],
                "correct": 0, "explanation": "", "topic": state["topic"],
            } for i in range(state["total_questions"])]

        return {"questions": questions}

    def _ask_question(self, state: QuizState) -> dict:
        questions = state.get("questions", [])
        current = state.get("current_question_index", 0)
        if current >= len(questions):
            return {"quiz_complete": True}

        q = questions[current]
        text = f"**第 {current+1}/{state['total_questions']} 题** ({q.get('topic','')})\n\n{q['question']}\n\n" + "\n".join(q["options"])
        return {"messages": [AIMessage(content=text)]}

    def _grade(self, state: QuizState) -> dict:
        questions = state.get("questions", [])
        current = state.get("current_question_index", 0)
        answers = list(state.get("answers", []))
        scores = list(state.get("scores", []))

        if current >= len(questions):
            return {"quiz_complete": True}

        # 找用户选择的答案
        selected = -1
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                try:
                    selected = int(str(m.content).strip())
                except ValueError:
                    pass
                break

        q = questions[current]
        correct_idx = q.get("correct", 0)
        is_correct = (selected == correct_idx)
        score = 1 if is_correct else 0

        answers.append(selected)
        scores.append(score)

        correct_option = q["options"][correct_idx] if correct_idx < len(q["options"]) else "?"
        feedback = "✅ **正确！**" if is_correct else f"❌ **错误** 正确答案是 **{correct_option}**"
        explanation = q.get("explanation", "")
        msg = f"{feedback}\n\n{explanation}" if explanation else feedback

        new_idx = current + 1

        return {
            "answers": answers, "scores": scores,
            "current_question_index": new_idx,
            "messages": [AIMessage(content=msg)],
        }

    def _final_report(self, state: QuizState) -> dict:
        scores = state.get("scores", [])
        total = state["total_questions"]
        correct = sum(scores)
        pct = correct / total * 100 if total else 0

        report = f"""## 📊 测验结果

**主题**: {state['topic']} | **难度**: {state['difficulty']}
**成绩**: {correct}/{total} ({pct:.0f}%)

### 逐题回顾
"""
        questions = state.get("questions", [])
        answers = state.get("answers", [])
        for i, (q, a) in enumerate(zip(questions, answers)):
            correct_idx = q.get("correct", 0)
            icon = "✅" if a == correct_idx else "❌"
            correct_text = q["options"][correct_idx] if correct_idx < len(q["options"]) else "?"
            report += f"{icon} **第{i+1}题**: {q['question'][:80]}... → 正确答案: {correct_text}\n\n"

        if pct >= 80:
            report += "\n🎉 表现优秀！基础知识扎实。"
        elif pct >= 60:
            report += "\n💪 不错的成绩，还有提升空间。"
        else:
            report += "\n📚 需要加强学习，建议重点复习错误的知识点。"

        return {"quiz_complete": True, "messages": [AIMessage(content=report)]}
