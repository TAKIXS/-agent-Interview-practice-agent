"""ChatPromptTemplate 构建器。"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def build_qa_prompt() -> ChatPromptTemplate:
    """构建知识问答的 ChatPromptTemplate。"""
    from src.prompts.system_prompts import QA_SYSTEM_PROMPT

    return ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])


def build_interview_setup_prompt() -> ChatPromptTemplate:
    """构建面试系统提示。"""
    from src.prompts.system_prompts import INTERVIEW_SYSTEM_PROMPT

    return ChatPromptTemplate.from_messages([
        ("system", INTERVIEW_SYSTEM_PROMPT),
        ("human", "请开始面试。"),
    ])


def build_evaluator_prompt() -> ChatPromptTemplate:
    """构建面试评估提示。"""
    from src.prompts.system_prompts import INTERVIEW_EVALUATOR_PROMPT

    return ChatPromptTemplate.from_messages([
        ("system", INTERVIEW_EVALUATOR_PROMPT),
        ("human", "请对以上回答进行评分。"),
    ])
