# Agent + RAG 集成

## 1. RAG 基础回顾

### 架构
```
文档 → 加载 → 分割 → Embedding → 向量库
查询 → 向量检索 → 取 Top-K → LLM 生成 → 回答
```

### Agent + RAG 的两种模式
| 模式 | 描述 | 适用场景 |
|------|------|----------|
| RAG as Tool | 检索作为 Agent 的一个工具 | 需要多个数据源的场景 |
| Agentic RAG | Agent 控制检索策略 | 复杂、多步推理场景 |

## 2. RAG as Tool（检索即工具）

```python
from langchain.tools import Tool

retriever_tool = Tool(
    name="knowledge_search",
    description="搜索内部知识库回答技术问题。输入为问题字符串。",
    func=lambda q: retriever.invoke(q),
)

# Agent 会自动判断什么时候用知识库搜索，什么时候用其他工具
agent = create_tool_calling_agent(llm, [retriever_tool, calculator, web_search], prompt)
```

### 多数据源检索
```python
tools = [
    Tool(name="java_docs", func=java_retriever.invoke,
         description="搜索 Java 技术文档"),
    Tool(name="agent_docs", func=agent_retriever.invoke,
         description="搜索 Agent 技术文档"),
    Tool(name="web_search", func=web_search_tool,
         description="搜索互联网最新信息"),
]
```

### 常见面试题
1. **Agent 什么时候应该用 RAG 而不是直接回答？** 需要专业知识/最新信息/企业内部数据时
2. **多个检索源如何让 Agent 正确选择？** 每个 tool 的描述写清楚领域和范围

## 3. Agentic RAG（Agent 驱动的检索）

### 自适应检索
```python
class AgenticRAG:
    def route(self, question: str) -> str:
        """根据问题类型选择检索策略"""
        if "代码" in question:
            return "code_search"
        elif "概念" in question:
            return "concept_search"
        elif "对比" in question:
            return "multi_search"  # 多路检索

    def multi_search(self, question: str):
        """并行检索多个源，合并去重"""
        results = parallel_search([source1, source2, source3], question)
        return rerank_and_merge(results)
```

### 检索策略
| 策略 | 说明 | 场景 |
|------|------|------|
| 单步检索 | 一次检索直接回答 | 简单事实型问题 |
| 多步检索 | 第一次检索 → 分析缺口 → 再次检索 | 需要推理的复杂问题 |
| 自适应检索 | 根据问题类型动态选择策略 | 混合型问题 |

### 常见面试题
1. **Agentic RAG 和普通 RAG 的区别？** Agentic RAG 的检索策略由 Agent 动态决定，而非固定的 pipeline
2. **如何评估 RAG 的检索质量？** 召回率/精确率、MRR、NDCG、Faithfulness（生成结果的忠实度）
3. **检索到无关文档怎么办？** Agent 自己判断文档是否相关，不相关则换关键词重搜

## 4. 高级 RAG 模式

### Self-RAG
- 检索后，LLM 先判断每个文档是否相关
- 无关文档过滤掉，只用相关文档生成
- 还可以标记"需要更好的检索"，触发二次搜索

### Corrective RAG
```python
def corrective_rag(question, retrieved_docs):
    grade = llm.grade_docs(question, retrieved_docs)  # 打分
    if grade < threshold:
        new_query = llm.rewrite_query(question)  # 改写查询
        retrieved_docs = retriever.invoke(new_query)
    return llm.generate(question, retrieved_docs)
```

### 常见面试题
1. **Self-RAG 的核心思想？** 让 LLM 自己评估检索质量，主动优化检索过程
2. **RAG 中如何处理多跳推理问题？** 分步检索（retrieve → answer → 发现缺口 → retrieve again）
