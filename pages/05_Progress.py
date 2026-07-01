"""学习进度页面 — 长期记忆驱动的个人学习画像。

功能：
- 主题熟练度雷达图
- 分数趋势折线图
- 学习时长统计
- 弱点分析 + 推荐学习路径
"""

import streamlit as st

st.title("📈 学习进度")
st.markdown("基于长期记忆追踪你的学习轨迹，发现优势与薄弱点。")

st.info("🏗️ 学习进度仪表盘将在 Phase 7 中实现。当前为框架占位。")

# 布局占位
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🎯 主题熟练度")
    st.markdown("*雷达图将在此处渲染...*")

with col2:
    st.markdown("### 📈 分数趋势")
    st.markdown("*趋势图将在此处渲染...*")

st.divider()

col3, col4 = st.columns(2)
with col3:
    st.markdown("### ⏱️ 学习统计")
    st.metric("总学习时长", "-- 小时")
    st.metric("完成会话数", "0")
    st.metric("累计答题数", "0")

with col4:
    st.markdown("### 💡 建议学习路径")
    st.markdown("*根据你的薄弱领域，这里将推荐学习内容...*")

# 侧边栏
with st.sidebar:
    st.markdown("### 📅 时间范围")
    st.selectbox("查看", ["最近 7 天", "最近 30 天", "全部"], key="progress_range")
