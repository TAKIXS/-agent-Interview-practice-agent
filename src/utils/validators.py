"""输入验证工具。"""

import os


def validate_api_config(provider: str, model_name: str, **custom_config) -> tuple[bool, str]:
    """验证给定的 API 配置是否完整。

    Returns:
        (is_valid, error_message)
    """
    if provider == "qwen" and not os.getenv("DASHSCOPE_API_KEY"):
        return False, "请在 .env 文件中设置 DASHSCOPE_API_KEY（阿里云 DashScope）"
    if provider == "deepseek" and not os.getenv("DEEPSEEK_API_KEY"):
        return False, "请在 .env 文件中设置 DEEPSEEK_API_KEY"
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        return False, "请在 .env 文件中设置 ANTHROPIC_API_KEY"
    if provider == "custom":
        if not custom_config.get("base_url"):
            return False, "自定义 API 必须填写 Base URL"
        if not model_name:
            return False, "自定义 API 必须填写模型名称"
    if not model_name:
        return False, "请选择或输入模型名称"
    return True, ""
