"""InterviewGraph — 模拟面试 LangGraph 状态机。

与 Streamlit 交互模式适配（每次用户回答触发一次 invoke）：

首次 invoke（启动）：
  setup -> ask_first_question -> END

后续 invoke（用户回答）：
  evaluate -> feedback -> conditional ->
      ask_next_question -> END（继续面试）
      final_report -> END（面试结束）
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.state.schemas import InterviewState

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SETUP_PROMPT = """你是一位资深技术面试官。请开始面试。

## 配置
- 主题：{topic}
- 难度：{difficulty}
- 总题数：{total_questions}

## 面试官行为
1. 自我介绍，说明面试安排（主题、题数）
2. 直接提出第一道题，难度与配置匹配
3. 每次只问一道题，等待回答
4. 用中文

只输出你的面试开场白 + 第一道题。"""

EVALUATE_FEEDBACK_PROMPT = """你是一位严格的面试评估专家。请对以下回答进行打分和反馈。

## 题目
{question}

## 面试者回答
{answer}

## 请完成两个任务：

### 第一步：评分（JSON格式）
```json
{{
    "technical_accuracy": 8.0,
    "depth": 7.5,
    "clarity": 9.0,
    "examples": 7.0,
    "overall": 7.9,
    "strengths": ["优点1"],
    "improvements": ["改进1"],
    "brief": "简短评语"
}}
```

### 第二步：反馈（直接文本）
给面试者的建设性反馈（100字内）：先肯定亮点，再指出改进方向。

### 第三步：下一题或结束
(如果是最后一题，标记 interview_complete=true 并给出结束语)

请先输出 JSON 评分（在 ```json 代码块中），再输出反馈文本。"""


# ---------------------------------------------------------------------------
# 主类
# ---------------------------------------------------------------------------

class InterviewGraph:
    """模拟面试 LangGraph 图。"""

    def __init__(self, llm: BaseChatModel, checkpointer, memory_context: str = "") -> None:
        self._llm = llm
        self._memory_context = memory_context
        self._graph = self._build().compile(checkpointer=checkpointer)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def start(self, thread_id: str, topic: str, difficulty: str, total: int) -> dict:
        """开始面试。返回面试官开场白 + 第一道题。"""
        config = {"configurable": {"thread_id": thread_id}}
        setup_data = json.dumps({
            "topic": topic, "difficulty": difficulty, "total_questions": total,
            "action": "start",
        }, ensure_ascii=False)
        return self._graph.invoke(
            {"messages": [HumanMessage(content=setup_data)]},
            config=config,
        )

    def answer(self, thread_id: str, user_answer: str) -> dict:
        """提交回答。返回评分 + 反馈 + 下一题（或最终报告）。"""
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(
            {"messages": [HumanMessage(content=user_answer)]},
            config=config,
        )

    def get_state(self, thread_id: str):
        return self._graph.get_state({"configurable": {"thread_id": thread_id}})

    # ------------------------------------------------------------------
    # 图构建
    # ------------------------------------------------------------------

    def _build(self) -> StateGraph:
        g = StateGraph(InterviewState)

        g.add_node("setup", self._setup)
        g.add_node("ask_first", self._ask_first)
        g.add_node("evaluate_feedback", self._evaluate_feedback)
        g.add_node("final_report", self._final_report)

        # 路由节点
        g.add_node("router", lambda s: {})

        g.set_entry_point("router")
        g.add_conditional_edges("router", self._route, {
            "setup": "setup",
            "evaluate": "evaluate_feedback",
            "end": END,
        })

        g.add_edge("setup", "ask_first")
        g.add_edge("ask_first", END)

        g.add_conditional_edges("evaluate_feedback", self._after_eval, {
            "final": "final_report",
            "end": END,
        })
        g.add_edge("final_report", END)

        return g

    # ------------------------------------------------------------------
    # 路由
    # ------------------------------------------------------------------

    def _route(self, state: InterviewState) -> Literal["setup", "evaluate", "end"]:
        total = state.get("total_questions", 0)
        current = state.get("current_question_index", 0)
        complete = state.get("interview_complete", False)

        if complete:
            return "end"
        if total == 0:
            return "setup"
        if current >= total:
            return "end"
        return "evaluate"

    def _after_eval(self, state: InterviewState) -> Literal["final", "end"]:
        total = state.get("total_questions", 0)
        current = state.get("current_question_index", 0)
        if current >= total:
            return "final"
        return "end"

    # ------------------------------------------------------------------
    # 节点
    # ------------------------------------------------------------------

    def _setup(self, state: InterviewState) -> dict:
        """解析配置，初始化。"""
        msgs = state["messages"]
        config_str = ""
        for m in reversed(msgs):
            if isinstance(m, HumanMessage):
                config_str = str(m.content)
                break
        try:
            cfg = json.loads(config_str)
        except json.JSONDecodeError:
            cfg = {"topic": "Java + Agent", "difficulty": "中级", "total_questions": 5}

        return {
            "topic": cfg["topic"],
            "difficulty": cfg["difficulty"],
            "total_questions": cfg["total_questions"],
            "current_question_index": 0,
            "questions_asked": [],
            "user_answers": [],
            "scores": [],
            "interview_complete": False,
        }

    def _ask_first(self, state: InterviewState) -> dict:
        """生成面试开场白 + 第一道题。"""
        prompt = SETUP_PROMPT.format(
            topic=state["topic"],
            difficulty=state["difficulty"],
            total_questions=state["total_questions"],
        )
        resp = self._llm.invoke(prompt)
        content = str(resp.content)

        # 提取第一道题到 questions_asked
        return {
            "messages": [AIMessage(content=content)],
            "questions_asked": [content],
        }

    def _evaluate_feedback(self, state: InterviewState) -> dict:
        """评估回答 + 生成反馈 + 下一题。"""
        questions = list(state.get("questions_asked", []))
        answers = list(state.get("user_answers", []))
        scores = list(state.get("scores", []))
        current = state.get("current_question_index", 0)
        total = state.get("total_questions", 5)
        topic = state.get("topic", "综合")

        # 找到最新用户回答
        latest_answer = ""
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                content = str(m.content)
                if "action" not in content:  # 跳过配置消息
                    latest_answer = content
                    break

        if not latest_answer or not questions:
            return {}

        current_q = questions[-1]
        answers.append(latest_answer)

        # LLM 评分+反馈+下一题
        prompt = EVALUATE_FEEDBACK_PROMPT.format(question=current_q, answer=latest_answer)
        resp = self._llm.invoke(prompt)
        resp_text = str(resp.content)

        # 解析 JSON 评分
        score = {
            "technical_accuracy": 7.0, "depth": 7.0, "clarity": 7.0,
            "examples": 7.0, "overall": 7.0,
            "strengths": [], "improvements": [], "brief": "",
        }
        try:
            if "```json" in resp_text:
                json_str = resp_text.split("```json")[1].split("```")[0]
                score = json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass

        scores.append(score)

        # 下一题（如果还有）
        new_idx = current + 1
        new_messages = [AIMessage(content=resp_text)]

        if new_idx < total:
            # 生成下一道题
            next_prompt = f"""上一题 {current_q}
面试者回答 {latest_answer[:200]}
得分 {score.get('overall',0):.1f}/10

请提出第{new_idx+1}道面试题。
主题：{topic}，难度：{state['difficulty']}
与已问题目不重复，逐步加深。
只输出题目。"""
            next_resp = self._llm.invoke(next_prompt)
            next_q = str(next_resp.content)
            questions.append(next_q)
            new_messages.append(AIMessage(content=next_q))

        return {
            "messages": new_messages,
            "user_answers": answers,
            "scores": scores,
            "questions_asked": questions,
            "current_question_index": new_idx,
        }

    def _final_report(self, state: InterviewState) -> dict:
        """生成最终面试报告。"""
        questions = state.get("questions_asked", [])
        scores = state.get("scores", [])
        topic = state.get("topic", "综合")
        total = state.get("total_questions", 0)

        if scores:
            avg = sum(s.get("overall", 0) for s in scores) / len(scores)
        else:
            avg = 0

        qa_list = []
        for i, (q, s) in enumerate(zip(questions, scores)):
            qa_list.append(f"第{i+1}题 | {s.get('overall',0):.1f}分 | {s.get('brief','')}")

        report_prompt = f"""生成面试最终报告。

主题：{topic} | 难度：{state['difficulty']} | 总题数：{total} | 均分：{avg:.1f}/10

答题记录：
{chr(10).join(qa_list)}

用 Markdown 输出：
1. 总体评价
2. 各题表现
3. 优势领域
4. 待提升
5. 学习建议"""

        resp = self._llm.invoke(report_prompt)

        return {
            "interview_complete": True,
            "messages": [AIMessage(content=str(resp.content))],
        }
