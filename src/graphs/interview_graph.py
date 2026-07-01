"""InterviewGraph — 模拟面试 LangGraph 状态机（简化版）。

流程：
  首次:  setup -> ask_first -> END
  答题:  evaluate -> conditional -> ask_next -> END (or final -> END)
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from src.state.schemas import InterviewState


class InterviewGraph:
    """模拟面试图。"""

    def __init__(self, llm: BaseChatModel, checkpointer, memory_context: str = "") -> None:
        self._llm = llm
        self._memory = memory_context
        self._graph = self._build().compile(checkpointer=checkpointer)

    def start(self, thread_id: str, topic: str, difficulty: str, total: int) -> dict:
        config = {"configurable": {"thread_id": thread_id}}
        data = json.dumps({"topic": topic, "difficulty": difficulty, "total_questions": total, "action": "start"}, ensure_ascii=False)
        return self._graph.invoke({"messages": [HumanMessage(content=data)]}, config=config)

    def answer(self, thread_id: str, user_answer: str) -> dict:
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke({"messages": [HumanMessage(content=user_answer)]}, config=config)

    def get_state(self, thread_id: str):
        return self._graph.get_state({"configurable": {"thread_id": thread_id}})

    # -- 构建 --

    def _build(self) -> StateGraph:
        g = StateGraph(InterviewState)
        g.add_node("setup", self._setup)
        g.add_node("ask_first", self._ask_first)
        g.add_node("evaluate", self._evaluate)
        g.add_node("ask_next", self._ask_next)
        g.add_node("final", self._final)
        g.add_node("router", lambda s: {})

        g.set_entry_point("router")
        g.add_conditional_edges("router", self._route, {"setup": "setup", "evaluate": "evaluate", "end": END})
        g.add_edge("setup", "ask_first")
        g.add_edge("ask_first", END)
        g.add_conditional_edges("evaluate", self._after_eval, {"ask": "ask_next", "final": "final", "end": END})
        g.add_edge("ask_next", END)
        g.add_edge("final", END)
        return g

    def _route(self, s: InterviewState) -> Literal["setup", "evaluate", "end"]:
        if s.get("interview_complete"):
            return "end"
        if s.get("total_questions", 0) == 0:
            return "setup"
        return "evaluate"

    def _after_eval(self, s: InterviewState) -> Literal["ask", "final", "end"]:
        total = s.get("total_questions", 0)
        current = s.get("current_question_index", 0)
        if s.get("interview_complete"):
            return "end"
        if current >= total:
            return "final"
        return "ask"

    # -- 节点 --

    def _setup(self, s: InterviewState) -> dict:
        for m in reversed(s["messages"]):
            if isinstance(m, HumanMessage):
                try:
                    cfg = json.loads(str(m.content))
                    return {"topic": cfg["topic"], "difficulty": cfg["difficulty"], "total_questions": cfg["total_questions"], "current_question_index": 0, "questions_asked": [], "user_answers": [], "scores": [], "interview_complete": False}
                except json.JSONDecodeError:
                    pass
        return {"topic": "综合", "difficulty": "中级", "total_questions": 5, "current_question_index": 0, "questions_asked": [], "user_answers": [], "scores": [], "interview_complete": False}

    def _ask_first(self, s: InterviewState) -> dict:
        prompt = f"""你是一位资深技术面试官。

面试主题：{s['topic']}
难度：{s['difficulty']}
总题数：{s['total_questions']}

请：
1. 简短自我介绍并说明面试安排
2. 直接提出第一道题
3. 只输出你的开场白+题目，不要自问自答"""

        resp = self._llm.invoke(prompt)
        q = str(resp.content)
        return {"messages": [AIMessage(content=q)], "questions_asked": [q]}

    def _evaluate(self, s: InterviewState) -> dict:
        questions = list(s.get("questions_asked", []))
        answers = list(s.get("user_answers", []))
        scores = list(s.get("scores", []))
        current_q = questions[-1] if questions else ""

        # 找最新用户回答
        latest_a = ""
        for m in reversed(s["messages"]):
            if isinstance(m, HumanMessage):
                txt = str(m.content)
                if "action" not in txt and not txt.startswith("{"):
                    latest_a = txt
                    break

        answers.append(latest_a)

        # 评分
        eval_prompt = f"""你是面试评估专家。对以下回答评分。

题目：{current_q}
回答：{latest_a}

输出 JSON（只输出 JSON，不要其他）：
{{"technical_accuracy":8.0,"depth":7.5,"clarity":9.0,"examples":7.0,"overall":7.9,"strengths":["亮点1"],"improvements":["改进1"],"brief":"简短评语(30字)"}}"""

        resp = self._llm.invoke(eval_prompt)
        try:
            txt = str(resp.content)
            if "```" in txt:
                txt = txt.split("```")[1]
                if txt.startswith("json"):
                    txt = txt[4:]
            score = json.loads(txt)
        except (json.JSONDecodeError, IndexError):
            score = {"technical_accuracy": 7, "depth": 7, "clarity": 7, "examples": 7, "overall": 7, "strengths": [], "improvements": [], "brief": ""}

        scores.append(score)
        new_idx = len(answers)  # 已经回答了的问题数

        # 生成简洁反馈
        fb_prompt = f"""给面试者简短反馈（80字内）。先肯定亮点，再指出改进方向。

题目：{current_q}
得分：{score.get('overall',0):.1f}/10
优点：{','.join(score.get('strengths',[]))}
改进：{','.join(score.get('improvements',[]))}"""

        fb = self._llm.invoke(fb_prompt)
        fb_text = f"**得分 {score.get('overall',0):.1f}/10**\n\n{str(fb.content)}"

        return {"user_answers": answers, "scores": scores, "current_question_index": new_idx, "messages": [AIMessage(content=fb_text)]}

    def _ask_next(self, s: InterviewState) -> dict:
        questions = list(s.get("questions_asked", []))
        total = s.get("total_questions", 5)
        current = s.get("current_question_index", 0)

        prev_qs = "\n".join(f"第{i+1}题: {q[:100]}" for i, q in enumerate(questions))

        prompt = f"""你是面试官。出第{current+1}题（共{total}题）。

主题：{s['topic']}  难度：{s['difficulty']}

已问题目：
{prev_qs}

要求：
- 与已问题目不重复
- 逐步加深难度
- 只输出题目本身，一行标题+一行题目描述"""

        resp = self._llm.invoke(prompt)
        next_q = str(resp.content)
        questions.append(next_q)

        return {"questions_asked": questions, "messages": [AIMessage(content=f"**第{current+1}/{total}题**\n\n{next_q}")]}

    def _final(self, s: InterviewState) -> dict:
        questions = s.get("questions_asked", [])
        scores = s.get("scores", [])
        total = s.get("total_questions", 0)
        avg = sum(x.get("overall", 0) for x in scores) / len(scores) if scores else 0

        qa = "\n".join(f"{i+1}. {q[:80]} | {sc.get('overall',0):.1f}分 | {sc.get('brief','')}" for i, (q, sc) in enumerate(zip(questions, scores)))

        report = self._llm.invoke(f"""生成面试最终报告。

主题：{s['topic']} | 难度：{s['difficulty']}
均分：{avg:.1f}/10 | 题数：{total}

{qa}

用 Markdown 输出：1总体评价 2各题表现 3优势 4待提升 5学习建议""")

        return {"interview_complete": True, "messages": [AIMessage(content=str(report.content))]}
