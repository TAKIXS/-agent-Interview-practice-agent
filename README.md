# LangChain 面试辅导 Agent

基于 LangChain + LangGraph + Streamlit 构建的 AI 面试辅导应用，覆盖 **Java 后端** 和 **LangChain Agent** 两大领域。

## 功能

| 功能 | 说明 |
|------|------|
| 💬 知识问答 | RAG 多轮对话，从知识库检索并回答技术问题 |
| 🎤 模拟面试 | AI 面试官出题 → 打分 → 反馈 → 报告 |
| 📝 知识测验 | AI 自动出选择题，逐题评分 + 成绩报告 |
| 🧠 智能路由 | 首页输入任意问题，自动识别意图并跳转 |

## 快速开始

```bash
# 1. 安装依赖（使用 uv）
uv venv
uv pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 启动
streamlit run app.py
```

## 架构

```
Streamlit UI (app.py + pages/)
       │
LangGraph Supervisor (Intent Classifier)
       │
  ┌────┼────┬────────┐
  QA   │  Quiz     Interview
Agent  │  Agent    Agent
       │
  RAG Pipeline (ChromaDB + HuggingFace Embeddings)
       │
Knowledge Base (11 Markdown docs: Java 5 + Agent 5)
```

## 项目结构

```
src/
├── agents/       # QA/Interview/Quiz/Classifier Agent
├── graphs/       # LangGraph 状态机
├── llm/          # LLM 抽象层（DeepSeek/千问/Anthropic/自定义）
├── rag/          # RAG 管道（Loader/Splitter/Embeddings/Store/Retriever）
├── memory/       # 长期记忆（SQLite 用户档案 + 熟练度追踪）
├── conversation/ # 多轮对话管理（线程 + 摘要）
├── prompts/      # 集中化 Prompt 管理
├── state/        # TypedDict 状态 Schema
├── scoring/      # Pydantic 评分模型
└── utils/        # 工具函数
```

## 支持的 LLM

| Provider | 默认 | 配置 |
|----------|------|------|
| DeepSeek | ✅ | `DEEPSEEK_API_KEY` |
| 通义千问 | | `DASHSCOPE_API_KEY` |
| Anthropic | | `ANTHROPIC_API_KEY` |
| 自定义 | | 任意 OpenAI 兼容 API |

## Embedding

默认使用 HuggingFace `all-MiniLM-L6-v2`（本地运行，免费）。
国内用户建议设置 `HF_ENDPOINT=https://hf-mirror.com` 使用镜像。

## License

MIT
