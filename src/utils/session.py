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
    """初始化 Streamlit session_state 中的所有 key。

    在整个 app 生命周期的每次 rerun 开始调用。只设置尚未存在的 key。
    """
    for key in _KEYS:
        if key not in st.session_state:
            st.session_state[key] = None
