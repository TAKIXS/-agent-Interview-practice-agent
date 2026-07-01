"""LLMFactory — 根据 provider + model_id 创建 LangChain BaseChatModel 实例。

支持四种 provider：
- qwen:     通义千问 (DashScope) — ChatOpenAI + 千问 base_url
- deepseek: DeepSeek — ChatOpenAI + DeepSeek base_url
- anthropic: Anthropic Claude — ChatAnthropic
- custom:    自定义 OpenAI 兼容 API — ChatOpenAI + 用户配置 base_url

千问和 DeepSeek 都是 OpenAI 兼容接口，底层统一使用 ChatOpenAI + 各自的 base_url。
"""

import os
from typing import Any

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

# ============================================================================
# 各 provider 的固定 base_url（从 models.yaml 读更优雅，这里做硬编码回退）
# ============================================================================
_OPENAI_COMPATIBLE_PROVIDERS: dict[str, dict[str, str]] = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
    },
}


class LLMFactory:
    """工厂模式创建 LLM 实例。"""

    _provider_registry: dict[str, str] = {
        "qwen": "_create_openai_compatible",
        "deepseek": "_create_openai_compatible",
        "anthropic": "_create_anthropic",
        "custom": "_create_custom",
    }

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        provider: str,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """创建 LLM 实例。

        Args:
            provider:    "qwen" | "deepseek" | "anthropic" | "custom"
            model_id:   模型 ID
            temperature: 采样温度
            max_tokens: 最大输出 token
            **kwargs:   custom provider 额外参数：base_url, api_key
        """
        if provider not in cls._provider_registry:
            supported = ", ".join(cls._provider_registry.keys())
            raise ValueError(
                f"不支持的 provider: '{provider}'。支持: {supported}"
            )

        factory_method = getattr(cls, cls._provider_registry[provider])
        return factory_method(provider, model_id, temperature, max_tokens, **kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """返回所有已注册的 provider 名称。"""
        return list(cls._provider_registry.keys())

    # ------------------------------------------------------------------
    # 各 provider 的创建方法
    # ------------------------------------------------------------------

    @classmethod
    def _create_openai_compatible(
        cls,
        provider: str,
        model_id: str,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """创建 OpenAI 兼容 API 的 LLM（千问 / DeepSeek）。

        从 _OPENAI_COMPATIBLE_PROVIDERS 读取预置的 base_url，
        从对应的环境变量读取 API Key。
        """
        from langchain_openai import ChatOpenAI

        config = _OPENAI_COMPATIBLE_PROVIDERS[provider]
        api_key = os.getenv(config["env_key"], "")

        return ChatOpenAI(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens or 8192,
            base_url=config["base_url"],
            api_key=api_key,
        )

    @classmethod
    def _create_anthropic(
        cls,
        provider: str,
        model_id: str,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """创建 Anthropic Claude LLM。"""
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            api_key=SecretStr(os.getenv("ANTHROPIC_API_KEY", "")),
        )

    @classmethod
    def _create_custom(
        cls,
        provider: str,
        model_id: str,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """创建自定义 OpenAI 兼容 API 的 LLM（Ollama / vLLM / ...）。

        通过 kwargs 传入 base_url 和 api_key。
        """
        from langchain_openai import ChatOpenAI

        base_url: str = kwargs.get("base_url", "")
        api_key: str = kwargs.get("api_key", "not-needed")

        if not base_url:
            raise ValueError("custom provider 必须提供 base_url 参数")

        return ChatOpenAI(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            base_url=base_url,
            api_key=api_key,
        )
