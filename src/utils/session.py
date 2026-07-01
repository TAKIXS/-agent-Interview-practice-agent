"""Streamlit session_state 管理助手。"""

from __future__ import annotations

import streamlit as st
from typing import Any

# 需要在 Session State 中保持的 key 名称
_KEYS = [
    "model_manager",
    "current_provider",
    "current_model",
    "current_temperature",
    "custom_base_url",
    "custom_api_key",
    "custom_model_name",
    "api_keys_configured",
]


def init_session_state() -> None:
    """初始化 Streamlit session_state 中的所有 key。"""
    for key in _KEYS:
        if key not in st.session_state:
            st.session_state[key] = None


def get_shared_llm():
    """获取共享 LLM 实例，自动应用侧边栏的模型选择。

    所有功能页应通过此函数获取 LLM，确保侧边栏切换模型后生效。
    """
    from src.llm.manager import ModelManager

    mgr = st.session_state.get("model_manager")
    if mgr is None:
        mgr = ModelManager()
        st.session_state.model_manager = mgr

    # 应用用户在侧边栏的选择
    provider = st.session_state.get("current_provider")
    model = st.session_state.get("current_model")
    temp = st.session_state.get("current_temperature", 0.7)

    if provider and model and (
        provider != mgr.current_provider
        or model != mgr.current_model
    ):
        mgr.switch_model(provider, model, temp)

    return mgr.llm
