"""意图分类器 — 分析用户输入，输出功能路由结果。

使用 LLM structured output 输出 {"intent": "qa"|"interview"|"code"|"quiz", "topic": str}
"""

import json
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

CLASSIFIER_PROMPT = """分析用户输入，判断用户想使用哪个功能。输出 JSON。

## 功能说明
- **qa**: 提问技术问题（Java、Agent 概念、原理等）
- **interview**: 想进行模拟面试练习
- **code**: 想动手写代码练习
- **quiz**: 想做知识测验/选择题

## 输出格式
{"intent": "qa", "topic": "Java基础"}  如果是 qa，尝试提取主题
{"intent": "interview", "topic": "Agent面试"}
{"intent": "quiz", "topic": "Java综合"}
{"intent": "code", "topic": "RAG"}

## 示例
用户: "什么是HashMap？" → {"intent": "qa", "topic": "Java集合"}
用户: "帮我模拟面试" → {"intent": "interview", "topic": "综合面试"}
用户: "我要做题" → {"intent": "quiz", "topic": "综合"}
用户: "怎么写一个RAG chain" → {"intent": "qa", "topic": "RAG"}

只输出 JSON，不要其他内容。"""


class IntentClassifier:
    """意图分类器。"""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    def classify(self, user_input: str) -> dict:
        """分析用户输入，返回意图和主题。

        Returns: {"intent": "qa|interview|code|quiz", "topic": "..."}
        """
        resp = self._llm.invoke([
            SystemMessage(content=CLASSIFIER_PROMPT),
            HumanMessage(content=user_input),
        ])
        text = str(resp.content).strip()

        try:
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text)
            return {
                "intent": result.get("intent", "qa"),
                "topic": result.get("topic", ""),
            }
        except (json.JSONDecodeError, KeyError):
            return {"intent": "qa", "topic": ""}
