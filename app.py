"""LangChain 面试辅导 Agent — Apple 极简风格首页。"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
from src.utils.logging_config import setup_logging
from src.utils.session import init_session_state
from config.settings import settings

setup_logging(settings.log_level)
settings.ensure_dirs()
init_session_state()

from src.llm.manager import ModelManager

if st.session_state.model_manager is None:
    st.session_state.model_manager = ModelManager()
mgr: ModelManager = st.session_state.model_manager

# ============================================================================
# 页面配置
# ============================================================================
st.set_page_config(
    page_title="Interview Coach",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# Apple 极简 CSS
# ============================================================================
st.html("""
<style>
/* 全局 — 使用系统字体，秒渲染 */
* { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; }

/* 隐藏 Streamlit 默认元素 */
#MainMenu, footer, .stDeployButton { display: none; }
header[data-testid="stHeader"] { background: transparent; }

/* 主容器 */
.main .block-container {
    max-width: 960px;
    padding-top: 3rem;
}

/* 标题 */
h1 { font-size: 3rem !important; font-weight: 700 !important; letter-spacing: -0.02em; color: #1D1D1F; }
h2 { font-size: 1.75rem !important; font-weight: 600 !important; color: #1D1D1F; }
h3 { font-size: 1.25rem !important; font-weight: 600 !important; color: #1D1D1F; }

/* 卡片 */
.apple-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 2rem 1.5rem;
    text-align: center;
    border: 1px solid #E8E8ED;
    transition: all 0.2s ease;
    cursor: pointer;
    height: 100%;
}
.apple-card:hover {
    border-color: #D1D1D6;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: #F5F5F7;
    border-right: 1px solid #E8E8ED;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    font-size: 1rem !important;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #86868B;
}

/* 全局按钮 */
.stButton > button {
    background: #F5F5F7;
    color: #0071E3;
    border: none;
    border-radius: 980px;
    padding: 0.45rem 1.1rem;
    font-weight: 500;
    font-size: 0.88rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #E8E8ED;
}
/* 主要按钮 (type=primary) */
.stButton > button[kind="primary"] {
    background: #0071E3;
    color: white;
}
.stButton > button[kind="primary"]:hover {
    background: #0077ED;
}

/* 输入框 */
.stTextInput > div > div > input {
    border-radius: 10px;
    border: 1px solid #D1D1D6;
    padding: 0.75rem 1rem;
    font-size: 1rem;
}

/* 选择框 */
.stSelectbox > div > div {
    border-radius: 10px;
}

/* 分割线 */
hr {
    border-color: #E8E8ED;
    margin: 2rem 0;
}

/* 右键消息 */
.stChatMessage {
    border-radius: 12px;
    padding: 0.5rem 0;
}

/* Charts 进度条 */
.stProgress > div > div {
    background: #0071E3;
}
</style>
""")

# ============================================================================
# 侧边栏
# ============================================================================
with st.sidebar:
    st.markdown("## 模型配置")
    providers = mgr.list_providers()
    provider_names = [p["name"] for p in providers]
    provider_keys = [p["key"] for p in providers]
    saved = st.session_state.current_provider or mgr.current_provider
    try:
        idx = provider_keys.index(saved)
    except ValueError:
        idx = 0

    selected_name = st.selectbox("服务商", provider_names, index=idx, label_visibility="collapsed")
    selected_key = provider_keys[provider_names.index(selected_name)]
    st.session_state.current_provider = selected_key

    if selected_key != "custom":
        models = mgr.list_models_for_provider(selected_key)
        if models:
            model_names = [m["name"] for m in models]
            model_ids = [m["id"] for m in models]
            st.session_state.current_model = model_ids[model_names.index(
                st.selectbox("模型", model_names, index=0, label_visibility="collapsed")
            )]

    st.divider()

    st.markdown("## 密钥状态")
    keys = {
        "DeepSeek": bool(os.getenv("DEEPSEEK_API_KEY")),
        "通义千问": bool(os.getenv("DASHSCOPE_API_KEY")),
    }
    for name, ok in keys.items():
        st.markdown(f"{'●' if ok else '○'} {name}")

    if st.button("应用配置", use_container_width=True):
        mgr.switch_model(selected_key, st.session_state.current_model, 0.7)
        st.success("已更新")


# ============================================================================
# 首页
# ============================================================================

st.html('<div style="height: 2rem"></div>')

st.title("Interview Coach")
st.html(
    '<p style="font-size:1.25rem;color:#86868B;margin-top:-0.5rem;margin-bottom:3rem;font-weight:400">'
    'AI 驱动的技术面试辅导 — 简洁、专注、高效'
    '</p>'
)

# 四张功能卡片
cols = st.columns(4)

cards = [
    ("问答", "知识问答", "基于 RAG 的智能问答\n覆盖 Java + Agent", "pages/01_Knowledge_QA.py"),
    ("面试", "模拟面试", "AI 面试官出题\n专业打分与反馈", "pages/02_Mock_Interview.py"),
    ("练习", "代码实战", "在线编写与执行\nAI 代码评审", "pages/03_Code_Practice.py"),
    ("测验", "知识测验", "自动出题\n逐题评分与报告", "pages/04_Knowledge_Quiz.py"),
]

for col, (icon, title, desc, page) in zip(cols, cards):
    with col:
        st.html(f"""
        <div class="apple-card" style="display:flex;flex-direction:column;min-height:200px">
            <div style="font-size:2rem;margin-bottom:0.75rem">{icon}</div>
            <div style="font-size:1.1rem;font-weight:600;color:#1D1D1F;margin-bottom:0.5rem">{title}</div>
            <div style="font-size:0.9rem;color:#86868B;line-height:1.5;white-space:pre-line;flex:1">{desc}</div>
        </div>
        """)
        if st.button(f"{title}  →", key=f"nav_{page}"):
            st.switch_page(page)

st.divider()

# 快捷输入
st.html('<p style="font-size:0.85rem;font-weight:600;color:#86868B;letter-spacing:0.04em;margin-bottom:0.5rem">快捷入口</p>')

quick_q = st.text_input(
    "quick_input",
    placeholder="输入任何问题，AI 自动识别意图并跳转 — 试试「HashMap 原理」或「帮我模拟面试」",
    label_visibility="collapsed",
)

if quick_q:
    try:
        from src.agents.classifier import IntentClassifier
        classifier = IntentClassifier(mgr.llm)
        result = classifier.classify(quick_q)
        page_map = {"qa": "pages/01_Knowledge_QA.py", "interview": "pages/02_Mock_Interview.py",
                    "code": "pages/03_Code_Practice.py", "quiz": "pages/04_Knowledge_Quiz.py"}
        st.switch_page(page_map.get(result.get("intent", "qa"), "pages/01_Knowledge_QA.py"))
    except Exception as e:
        st.warning(f"意图识别暂不可用：{e}")

st.html('<p style="text-align:center;color:#C7C7CC;font-size:0.8rem;margin-top:3rem">Made for learning · Not for production</p>')
