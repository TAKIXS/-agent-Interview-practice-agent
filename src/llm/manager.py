"""ModelManager — 运行时模型切换，读取 config/models.yaml，管理当前 LLM 实例。

功能：
- 从 YAML 配置加载所有可用 provider 和模型
- 懒加载 LLM 实例（切换模型时自动重建）
- 提供 UI 所需的数据结构（list_providers / list_models_for_provider）
- 管理自定义 provider 的额外配置（base_url / api_key）

支持 provider：qwen / deepseek / anthropic / custom
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from langchain_core.language_models import BaseChatModel

from src.llm.factory import LLMFactory


# 非 OpenAI 兼容的原生 provider（走各自 SDK）
_NATIVE_PROVIDERS = {"anthropic"}


class ModelManager:
    """管理 LLM 生命周期和运行时切换。"""

    def __init__(self, config_path: str = "config/models.yaml") -> None:
        self._config_path = Path(config_path)
        self._config: dict[str, Any] = self._load_config()

        # 当前选中（从 YAML defaults 读取）
        defaults = self._config.get("defaults", {})
        self.current_provider: str = defaults.get("provider", "qwen")
        self.current_model: str = defaults.get("model", "qwen-plus-latest")
        self.current_temperature: float = defaults.get("temperature", 0.7)

        # custom provider 的额外配置（由用户在 UI 中输入）
        self._custom_config: dict[str, str] = {}

        # 缓存的 LLM 实例
        self._llm: BaseChatModel | None = None

    # ------------------------------------------------------------------
    # 公开属性
    # ------------------------------------------------------------------

    @property
    def llm(self) -> BaseChatModel:
        """获取当前 LLM 实例（懒加载，切换模型后自动重建）。"""
        if self._llm is None:
            self._llm = self._build_llm()
        return self._llm

    # ------------------------------------------------------------------
    # 切换
    # ------------------------------------------------------------------

    def switch_model(
        self,
        provider: str,
        model_id: str,
        temperature: float = 0.7,
        **custom_config: str,
    ) -> None:
        """切换当前使用的模型。切换后 llm 属性返回新实例。

        Args:
            provider:          "qwen" | "deepseek" | "anthropic" | "custom"
            model_id:          模型 ID
            temperature:       温度
            **custom_config:   仅 custom provider 需要：base_url, api_key
        """
        self.current_provider = provider
        self.current_model = model_id
        self.current_temperature = temperature
        self._custom_config = custom_config
        self._llm = None  # 失效缓存，下次访问时重建

    # ------------------------------------------------------------------
    # UI 数据
    # ------------------------------------------------------------------

    def list_providers(self) -> list[dict[str, Any]]:
        """返回所有 provider 的 UI 展示数据。

        Returns: [{"key": "qwen", "name": "通义千问"}, ...]
        """
        providers_data = self._config.get("providers", {})
        return [
            {"key": key, "name": data.get("display_name", key)}
            for key, data in providers_data.items()
        ]

    def list_models_for_provider(self, provider: str) -> list[dict[str, Any]]:
        """返回某 provider 下所有预设模型。

        qwen / deepseek / anthropic 有预设模型列表。
        custom 返回空列表（模型名由用户自由输入）。

        Returns: [{"id": "qwen-plus-latest", "name": "Qwen Plus", "max_tokens": 8192}, ...]
        """
        providers_data = self._config.get("providers", {})
        provider_data = providers_data.get(provider, {})
        return provider_data.get("models", [])

    def get_provider_config_fields(self, provider: str) -> list[dict[str, Any]]:
        """返回某 provider 的自定义配置字段。

        仅 custom provider 需要用户在 UI 中填写额外配置。
        其他 provider 返回空列表。
        """
        providers_data = self._config.get("providers", {})
        provider_data = providers_data.get(provider, {})
        return provider_data.get("config_fields", [])

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _load_config(self) -> dict[str, Any]:
        """加载并解析 YAML 配置文件。"""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"模型配置文件不存在: {self._config_path.resolve()}"
            )
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _build_llm(self) -> BaseChatModel:
        """通过 LLMFactory 构建当前 LLM 实例。"""
        model_info = self._get_model_info(self.current_provider, self.current_model)
        default_max_tokens = model_info.get("max_tokens") if model_info else None

        if self.current_provider == "custom":
            return LLMFactory.create(
                provider=self.current_provider,
                model_id=self.current_model,
                temperature=self.current_temperature,
                max_tokens=default_max_tokens,
                base_url=self._custom_config.get("base_url", ""),
                api_key=self._custom_config.get("api_key", ""),
            )
        else:
            return LLMFactory.create(
                provider=self.current_provider,
                model_id=self.current_model,
                temperature=self.current_temperature,
                max_tokens=default_max_tokens,
            )

    def _get_model_info(self, provider: str, model_id: str) -> dict[str, Any] | None:
        """从 YAML 中查找某模型的配置信息。"""
        providers_data = self._config.get("providers", {})
        provider_data = providers_data.get(provider, {})
        for model in provider_data.get("models", []):
            if model.get("id") == model_id:
                return model
        return None
