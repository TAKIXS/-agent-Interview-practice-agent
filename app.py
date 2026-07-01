"""LangChain 面试辅导 Agent — Streamlit 入口。

提供：
- 侧边栏：模型选择（Anthropic / OpenAI / 自定义 API） + 温度调节
- 首页：四大功能入口 + 快速提问
- 全局 session_state 初始化
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# --- 环境 & 日志 ---
load_dotenv()
from src.utils.logging_config import setup_logging
from src.utils.session import init_session_state
from config.settings import settings

setup_logging(settings.log_level)
settings.ensure_dirs()

# ============================================================================
# 页面配置
# ============================================================================
st.set_page_config(
    page_title="LangChain 面试辅导 Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Session State 初始化
# ============================================================================
init_session_state()

from src.llm.manager import ModelManager

# ModelManager 单例（缓存）
if st.session_state.model_manager is None:
    st.session_state.model_manager = ModelManager()

mgr: ModelManager = st.session_state.model_manager


# ============================================================================
# 辅助函数
# ============================================================================

def check_api_keys() -> dict[str, bool]:
    """检查主要 provider 的 API Key 是否已配置。"""
    return {
        "通义千问": bool(os.getenv("DASHSCOPE_API_KEY", "")),
        "DeepSeek": bool(os.getenv("DEEPSEEK_API_KEY", "")),
        "Anthropic": bool(os.getenv("ANTHROPIC_API_KEY", "")),
    }


# ============================================================================
# 侧边栏 — 模型配置
# ============================================================================

st.sidebar.title("⚙️ 模型配置")

# --- API Key 状态指示 ---
st.sidebar.markdown("### 🔑 API Key 状态")
keys = check_api_keys()
for name, configured in keys.items():
    icon = "🟢" if configured else "🔴"
    st.sidebar.markdown(f"{icon} **{name}**")

if not any(keys.values()):
    st.sidebar.warning("请先在 .env 中配置 API Key（千问 / DeepSeek / Anthropic）")

# --- Provider 选择 ---
st.sidebar.markdown("### 🤖 模型选择")
providers = mgr.list_providers()
provider_names = [p["name"] for p in providers]
provider_keys = [p["key"] for p in providers]

# 恢复已保存的选择
saved_provider = st.session_state.current_provider or mgr.current_provider
try:
    provider_idx = provider_keys.index(saved_provider)
except ValueError:
    provider_idx = 0

selected_provider_name = st.sidebar.selectbox(
    "Provider",
    provider_names,
    index=provider_idx,
    key="provider_selector",
)
selected_provider_key = provider_keys[provider_names.index(selected_provider_name)]
st.session_state.current_provider = selected_provider_key

# --- Model 选择（仅 anthropic / openai 显示下拉） ---
if selected_provider_key != "custom":
    models = mgr.list_models_for_provider(selected_provider_key)
    model_names = [m["name"] for m in models] if models else []
    model_ids = [m["id"] for m in models] if models else []

    saved_model = st.session_state.current_model or mgr.current_model
    try:
        model_idx = model_ids.index(saved_model)
    except ValueError:
        model_idx = 0

    if model_names:
        selected_model_name = st.sidebar.selectbox(
            "Model",
            model_names,
            index=model_idx,
            key="model_selector",
        )
        st.session_state.current_model = model_ids[model_names.index(selected_model_name)]
    else:
        st.sidebar.warning("无可用模型")
else:
    # Custom provider：用户输入
    st.sidebar.markdown("#### 自定义 API 配置")
    config_fields = mgr.get_provider_config_fields("custom")
    for field in config_fields:
        value = st.sidebar.text_input(
            field["label"],
            type=field.get("type", "text"),
            placeholder=field.get("placeholder", ""),
            key=f"custom_{field['name']}",
        )
        if field["name"] == "base_url":
            st.session_state.custom_base_url = value
        elif field["name"] == "api_key":
            st.session_state.custom_api_key = value
        elif field["name"] == "model_name":
            st.session_state.custom_model_name = value
    st.session_state.current_model = st.session_state.custom_model_name or ""

# --- 温度 ---
st.session_state.current_temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=2.0,
    value=0.7,
    step=0.1,
    key="temperature_slider",
)

# --- 应用配置 ---
if st.sidebar.button("🔄 应用配置"):
    if selected_provider_key == "custom":
        mgr.switch_model(
            provider="custom",
            model_id=st.session_state.current_model,
            temperature=st.session_state.current_temperature,
            base_url=st.session_state.custom_base_url or "",
            api_key=st.session_state.custom_api_key or "",
        )
    else:
        mgr.switch_model(
            provider=selected_provider_key,
            model_id=st.session_state.current_model,
            temperature=st.session_state.current_temperature,
        )
    st.sidebar.success(f"✅ 已切换到 {selected_provider_name} / {st.session_state.current_model}")

st.sidebar.divider()
st.sidebar.caption("LangChain 面试辅导 Agent v0.1.0")


# ============================================================================
# 首页内容
# ============================================================================

# 标题区
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🤖 LangChain 面试辅导 Agent")
    st.markdown("全方位准备 LangChain 技术面试 — 从概念理解到代码实战")

with col_status:
    provider_display = selected_provider_name
    model_display = st.session_state.current_model or "(未选择)"
    st.metric("当前模型", f"{provider_display} / {model_display}")

st.divider()

# 功能卡片
st.markdown("### 🚀 选择学习模式")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="background:#f0f4ff; padding:20px; border-radius:10px; text-align:center;">
        <h2>💬</h2>
        <h3>知识问答</h3>
        <p>基于 RAG 的智能问答，覆盖 LangChain 全栈知识点</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/01_Knowledge_QA.py", label="进入知识问答 →")

with col2:
    st.markdown("""
    <div style="background:#fff8f0; padding:20px; border-radius:10px; text-align:center;">
        <h2>🎤</h2>
        <h3>模拟面试</h3>
        <p>真实面试体验，AI 面试官出题 + 打分 + 反馈</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/02_Mock_Interview.py", label="进入模拟面试 →")

with col3:
    st.markdown("""
    <div style="background:#f0fff4; padding:20px; border-radius:10px; text-align:center;">
        <h2>💻</h2>
        <h3>代码实战</h3>
        <p>动手写代码，在线执行 + AI 评审 + 迭代改进</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/03_Code_Practice.py", label="进入代码实战 →")

with col4:
    st.markdown("""
    <div style="background:#fff0f4; padding:20px; border-radius:10px; text-align:center;">
        <h2>📝</h2>
        <h3>知识测验</h3>
        <p>AI 自动出题，选择题 + 详解 + 弱点追踪</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/04_Knowledge_Quiz.py", label="进入知识测验 →")

st.divider()

# 快速提问（智能路由）
st.markdown("### ⚡ 快速提问")
quick_q = st.text_input(
    "输入你的问题，AI 会自动判断意图并跳转到合适功能...",
    placeholder="试试：HashMap 原理？ / 帮我模拟面试 / 我要做题 / 什么是 Agent？",
)
if quick_q:
    try:
        from src.agents.classifier import IntentClassifier
        classifier = IntentClassifier(mgr.llm)
        result = classifier.classify(quick_q)
        intent = result.get("intent", "qa")
        st.success(f"识别意图: **{intent}** → 正在跳转...")

        page_map = {
            "qa": "pages/01_Knowledge_QA.py",
            "interview": "pages/02_Mock_Interview.py",
            "code": "pages/03_Code_Practice.py",
            "quiz": "pages/04_Knowledge_Quiz.py",
        }
        target = page_map.get(intent, "pages/01_Knowledge_QA.py")
        st.switch_page(target)
    except Exception as e:
        st.warning(f"路由暂不可用（{e}），请手动点击功能卡片。")

st.divider()
st.caption("💡 提示：在侧边栏切换模型后，点击「应用配置」生效。支持通义千问、DeepSeek、Anthropic Claude 及自定义 API。")
