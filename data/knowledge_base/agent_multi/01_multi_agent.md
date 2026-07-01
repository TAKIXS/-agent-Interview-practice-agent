# 多 Agent 系统

## 1. 多 Agent 架构模式

### 为什么需要多 Agent
- 单一 Agent 处理复杂任务时 Prompt 太长、工具太多，性能下降
- 不同领域需要不同的 System Prompt + 工具集
- 并行处理提高效率

### 架构模式对比
| 模式 | 描述 | 适用场景 |
|------|------|----------|
| Supervisor | 一个主 Agent 调度多个子 Agent | 任务明确可分派 |
| Hierarchical | 多层 Supervisor 树形结构 | 复杂组织架构 |
| Collaborative | 多 Agent 平等对话协作 | 创造性任务 |
| Debate | Agent 之间辩论得出结论 | 需要多角度验证 |

## 2. Supervisor 模式

```python
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_supervisor_agent

# 定义子 Agent
java_agent = create_agent(llm, java_tools, "你是 Java 专家")
agent_agent = create_agent(llm, agent_tools, "你是 Agent 专家")

# Supervisor 调度
supervisor = create_supervisor_agent(
    llm=llm,
    agents=[java_agent, agent_agent],
    prompt="将问题分配给最合适的专家回答",
)

# 图结构
# supervisor → java_agent → supervisor → agent_agent → END
```

### Supervisor 的 Prompt 设计
```
你是协调者。根据用户问题，选择最合适的专家：
- java_agent：Java 技术问题、Spring、JVM、并发
- agent_agent：LangChain Agent、RAG、多 Agent 系统

输出格式：
{"next": "java_agent"}  # 转接给 Java 专家
{"next": "FINISH"}      # 任务完成
```

### 常见面试题
1. **Supervisor 模式有什么缺点？** 单点瓶颈、额外 token 消耗、调度错误风险
2. **如何防止 Supervisor 在 Agent 之间来回切换死循环？** 设置最大切换次数、要求每次切换必须有新的信息

## 3. 多 Agent 协作模式

### 顺序协作（Pipeline）
```
Agent A（需求分析）→ Agent B（代码生成）→ Agent C（代码审查）
```
每个 Agent 只做一件事，输出传给下一个。

### 并行协作（Fan-out）
```
           ┌→ Agent Java →┐
用户问题 → ┤→ Agent RAG  →├→ 合并 → Supervisor 合成
           └→ Agent Test →┘
```

### 群聊（Group Chat）
```python
# AutoGen 风格的多 Agent 对话
group_chat = GroupChat(
    agents=[java_expert, agent_expert, reviewer],
    speaker_selection_method="round_robin",  # 轮转
    max_round=10,
)
```

### 常见面试题
1. **多 Agent 的通信方式有哪些？** 共享状态（LangGraph）、消息传递（AutoGen）、工具调用（CrewAI）
2. **如何避免 Agent 之间的信息丢失？** 统一的状态 Schema、关键信息结构化传递、设置信息摘要节点

## 4. LangGraph 多 Agent 实现

### 子图 (Subgraph)
```python
# 每个 Agent 是独立的 StateGraph
java_graph = create_java_agent_graph()
agent_graph = create_agent_agent_graph()

# Supervisor 图调用子图
supervisor_graph.add_node("java_expert", java_graph.compile())
supervisor_graph.add_node("agent_expert", agent_graph.compile())
```

### 共享状态
```python
class MultiAgentState(TypedDict):
    messages: list          # 对话历史
    current_agent: str      # 当前活跃的 Agent
    task_result: dict       # 各 Agent 的结果汇总
    next_step: str          # 下一步路由
```

### 常见面试题
1. **LangGraph 子图和普通函数节点的区别？** 子图有自己的内部状态机，可独立执行多步推理
2. **多 Agent 系统的 token 成本如何控制？** 小模型做路由、上下文压缩、只传递必要信息
