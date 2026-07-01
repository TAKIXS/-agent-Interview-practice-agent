# LangChain Agent 基础

## 1. Agent 是什么

### 核心概念
Agent 是将 **LLM 作为推理引擎**，让它自主决定**使用什么工具、以什么顺序、何时停止**的系统。

```
用户输入 → LLM 推理 → 决定调用工具 → 工具返回结果 → LLM 再推理 → ... → 最终回答
```

### Agent vs Chain 的本质区别
| 维度 | Chain | Agent |
|------|-------|-------|
| 执行路径 | 预定义的固定流程 | 动态决策 |
| 工具使用 | 不调用外部工具 | 可以调用任意工具 |
| 适应性 | 只能处理预设场景 | 处理未知/开放性任务 |
| 控制 | 开发者完全控制 | LLM 自主决策 |

### Agent 工作流程（ReAct 模式）
1. **Thought（思考）**：分析当前状态，决定下一步
2. **Action（行动）**：调用具体工具
3. **Observation（观察）**：接收工具返回结果
4. **循环**：重复以上步骤直到得出最终答案

## 2. Agent 类型

### 2.1 ReAct Agent
- 最早、最经典的 Agent 模式
- Prompt 中强制 LLM 输出 `Thought/Action/Observation` 格式
- 优点：可解释性强，每步都可追踪
- 缺点：Prompt 模板固定，灵活性有限

```python
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "北京今天天气怎么样？"})
```

### 2.2 OpenAI Functions / Tool Calling Agent
- 利用 LLM 原生的 function calling 能力
- LLM 直接返回结构化的函数调用 JSON
- 更可靠，减少格式解析错误

```python
from langchain.agents import create_tool_calling_agent

agent = create_tool_calling_agent(llm, tools, prompt)
```

### 2.3 Structured Chat Agent
- 支持多参数工具的 Agent
- 使用结构化 Chat 格式组织对话

### 常见面试题
1. **ReAct Agent 和 Tool Calling Agent 的区别？** ReAct 靠 Prompt 约束输出格式，Tool Calling 靠模型原生能力
2. **AgentExecutor 的核心参数有哪些？** agent, tools, max_iterations, handle_parsing_errors, early_stopping_method
3. **Agent 死循环怎么办？** 设置 max_iterations + early_stopping_method

## 3. AgentExecutor 内部机制

### 核心循环
```python
while not finished and iterations < max_iterations:
    # 1. 调用 Agent 规划下一步
    output = agent.plan(intermediate_steps, **inputs)

    # 2. 判断：是最终答案还是需要调用工具？
    if isinstance(output, AgentFinish):
        return output.return_values
    else:  # AgentAction
        # 3. 执行工具
        observation = tool.run(output.tool_input)
        # 4. 记录步骤
        intermediate_steps.append((output, observation))
```

### 关键参数
- `max_iterations`：最大执行步数，防止无限循环（默认 15）
- `handle_parsing_errors`：LLM 输出格式错误时的处理策略
- `early_stopping_method`：达到 max_iterations 时的行为（"force" 强制结束 / "generate" 生成答案）

## 4. 自定义 Agent

### 何时需要自定义 Agent
- 需要特殊的 Prompt 格式
- 需要 LangGraph 构建复杂状态机
- 需要 Human-in-the-loop 中断审批

### 使用 LangGraph 构建（推荐）
```python
from langgraph.graph import StateGraph, END

# 定义状态
class AgentState(TypedDict):
    messages: list
    next_step: str

# 定义节点
def agent_node(state): ...    # LLM 推理
def tool_node(state): ...     # 工具执行

# 构建图
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_conditional_edges("agent", should_continue, {
    "continue": "tools",
    "end": END
})
graph.add_edge("tools", "agent")  # 工具执行后回到 agent
graph.set_entry_point("agent")
```

### 常见面试题
1. **什么场景下 AgentExecutor 不够用？** 需要条件分支、并行执行、子 Agent、人工审批时
2. **LangGraph 相比 AgentExecutor 的优势？** 显式状态管理、条件路由、流式输出、可恢复
3. **Agent 的 token 消耗如何优化？** 压缩 intermediate_steps、用较小的模型做工具选择
