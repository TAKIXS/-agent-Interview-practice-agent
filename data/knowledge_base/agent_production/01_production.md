# Agent 生产部署与最佳实践

## 1. 部署架构

### LangServe
```python
from langserve import add_routes

# 将 Agent 部署为 REST API
add_routes(app, agent_executor, path="/agent")
# 自动生成 /agent/playground/ 测试页面
```

### 生产部署考量
| 维度 | 方案 | 说明 |
|------|------|------|
| 并发 | FastAPI + uvicorn workers | 多 worker 处理并发请求 |
| 负载均衡 | Nginx / K8s Service | 分发流量到多实例 |
| 缓存 | Redis | 缓存常见问题的响应 |
| 限流 | 令牌桶 / 滑动窗口 | 防止 API 超额 |
| 监控 | LangSmith / Prometheus | 追踪调用链、token 消耗 |

### 常见面试题
1. **Agent 服务如何横向扩展？** 无状态 Agent + 外部 checkpointer（PostgreSQL/Redis）+ K8s HPA
2. **如何保证 Agent 服务的高可用？** 多副本部署 + 健康检查 + 熔断降级

## 2. 安全与风险控制

### 输出安全
```python
# 输出审查
from langchain.callbacks import OutputGuardrailHandler

class SensitiveInfoGuardrail:
    def check(self, output: str) -> bool:
        # 检测是否包含敏感信息
        patterns = [r'\b\d{18}\b', r'\b密码\b']  # 身份证号等
        return not any(re.search(p, output) for p in patterns)
```

### 权限控制
```python
# 工具级别的权限控制
class SecuredTool(BaseTool):
    def _run(self, query: str, user_role: str) -> str:
        if user_role != "admin":
            return "权限不足"
        return actual_run(query)
```

### 安全最佳实践
1. **输入过滤**：防止 Prompt 注入攻击
2. **工具白名单**：限制 Agent 可调用的工具范围
3. **人工审批**：危险操作前要求人工确认
4. **输出审计**：记录所有 Agent 的决策和工具调用

### 常见面试题
1. **如何防止 Prompt 注入？** 输入分隔符、角色严格限定（System Prompt 优先于 User Prompt）、输入长度限制
2. **Agent 误调了危险工具怎么办？** Human-in-the-loop 审批、工具分级（读/写/删除）、操作回滚

## 3. 性能优化

### Token 管理
```python
# 压缩中间步骤
def compress_intermediate_steps(steps: list) -> str:
    """压缩工具调用历史，只保留关键信息"""
    summary = []
    for action, observation in steps:
        summary.append(f"Tool: {action.tool}, Result: {observation[:200]}")
    return "\n".join(summary)
```

### 缓存策略
```python
from langchain.cache import RedisCache
# 相同输入不重复调用 LLM
langchain.llm_cache = RedisCache(redis_client)
```

### 流式输出
```python
async for event in agent.astream_events({"input": "..."}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        yield event["data"]["chunk"].content  # 逐 token 输出
```

### 常见面试题
1. **Agent 响应太慢如何优化？** 用小模型做路由/工具选择、缓存、并行工具调用、流式输出
2. **一次 Agent 调用消耗大量 token 怎么办？** 限制 max_iterations、压缩上下文、选择性的保留 intermediate_steps

## 4. 评估与测试

### Agent 评估维度
| 维度 | 指标 | 方法 |
|------|------|------|
| 任务完成率 | 是否达成用户目标 | 人工标注 / LLM Judge |
| 效率 | 平均步数、token 消耗 | 统计分析 |
| 工具选择准确性 | 是否选择了正确的工具 | 测试用例 |
| 鲁棒性 | 异常输入处理 | 边界测试 |

### 测试策略
```python
def test_agent_tool_selection():
    """测试 Agent 是否选择了正确的工具"""
    inputs = [
        ("北京天气", "get_weather"),
        ("1+1等于几", "calculator"),
    ]
    for query, expected_tool in inputs:
        result = agent.invoke({"input": query})
        assert result["tool_used"] == expected_tool
```

### 常见面试题
1. **Agent 如何做回归测试？** 固定测试集 + LangSmith 录制回放 + 对比新旧版本输出
2. **如何评估 Agent 生成质量？** Faithfulness（忠实度）、Answer Relevance（回答相关性）、Context Precision（上下文精确度）
