# Agent 工具与集成

## 1. 工具 (Tools) 核心概念

### 工具定义
工具是 Agent 与外部世界交互的接口——搜索、计算、API 调用、数据库查询等。

```python
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """搜索互联网获取最新信息。"""
    return f"搜索结果: {query} ..."

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。"""
    return str(eval(expression))
```

### 工具描述的重要性
- LLM 靠工具的描述（docstring）来决定用哪个工具
- 描述应明确：**做什么、什么时候用、输入输出格式**
- 避免歧义描述：不说"获取数据"，说"通过 SQL 查询 MySQL 数据库获取用户订单数据"

### 常见面试题
1. **工具描述应该包含什么信息？** 功能说明、使用场景、参数含义、返回格式
2. **几十个工具时 LLM 怎么选？** 靠工具描述的语义匹配，可以将工具分组/分步选择

## 2. Function Calling 机制

### 工作原理
```
用户: "北京天气"
→ LLM 返回: {function: "get_weather", arguments: {city: "北京"}}
→ Agent 调用 get_weather(city="北京")
→ LLM 接收: "北京 25°C 晴"
→ 最终回答: "北京今天 25°C，晴天"
```

### 结构化工具定义
```python
from langchain_core.tools import StructuredTool

def get_weather(city: str, date: str = "today") -> dict:
    """查询指定城市天气。"""
    return {"city": city, "date": date, "temp": 25, "condition": "晴"}

weather_tool = StructuredTool.from_function(
    func=get_weather,
    name="get_weather",
    description="查询指定城市的天气，参数 city 为城市名，date 为日期(可选)"
)
```

### 常见面试题
1. **Function Calling 和 Prompt Engineering 选工具的区别？** FC 是模型原生 JSON 输出，更可靠；Prompt 靠正则解析，容易格式错误
2. **工具调用失败怎么办？** 设置 max_retries、给 LLM 返回错误信息让它重试、handle_parsing_errors=True

## 3. 内置工具与自定义工具

### 常用内置工具
```python
# 搜索工具
from langchain_community.tools import TavilySearchResults
# 代码解释器
from langchain.tools import PythonREPLTool
# 文件操作
from langchain_community.tools import FileManagementTool
```

### 自定义工具最佳实践
```python
class DatabaseTool(BaseTool):
    name = "database_query"
    description = "执行 SQL 查询。输入为 SQL 语句字符串。"

    def _run(self, query: str) -> str:
        # 实际查询数据库
        result = db.execute(query)
        return str(result)

    # 可选：异步版本
    async def _arun(self, query: str) -> str:
        return self._run(query)
```

### 工具设计原则
1. **单一职责**：一个工具只做一件事
2. **幂等性**：GET 类操作可重复调用不影响结果
3. **错误返回**：返回具体错误信息（而非断言失败），让 LLM 据此调整

### 常见面试题
1. **工具太多怎么办？** 分组为 Toolkits、用 Router Agent 先分类再分发
2. **工具的输入输出如何设计？** 输入尽量简单（LLM 容易生成），输出结构化且有上下文
3. **如何处理工具调用耗时过长？** 使用异步工具 (_arun)、设置超时、流式返回中间结果
