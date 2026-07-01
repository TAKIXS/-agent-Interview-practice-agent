"""EmbeddingProvider — 统一 embedding 接口。

支持三种 provider：
- openai:       text-embedding-3-small（需要 OPENAI_API_KEY）
- huggingface:  sentence-transformers（本地运行，免费）
- qwen:         千问 DashScope embedding（需要 DASHSCOPE_API_KEY）
- custom:       自定义 OpenAI 兼容 embedding endpoint
"""

import os
from typing import Protocol

from langchain_core.embeddings import Embeddings


class EmbeddingProvider:
    """根据配置创建 Embedding 实例。

    使用方式：
        provider = EmbeddingProvider(kind="huggingface")
        embeddings = provider.get()
    """

    def __init__(
        self,
        kind: str = "huggingface",
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.kind = kind
        self.model = model
        self.base_url = base_url
        self.api_key = api_key

    def get(self) -> Embeddings:
        """返回 LangChain Embeddings 实例。"""
        if self.kind == "openai":
            return self._create_openai()
        elif self.kind == "huggingface":
            return self._create_huggingface()
        elif self.kind == "qwen":
            return self._create_qwen()
        elif self.kind == "custom":
            return self._create_custom()
        else:
            raise ValueError(
                f"不支持的 embedding provider: '{self.kind}'。"
                f"支持: openai / huggingface / qwen / custom"
            )

    # ------------------------------------------------------------------
    # 各 provider 创建方法
    # ------------------------------------------------------------------

    def _create_openai(self) -> Embeddings:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=self.model or "text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )

    def _create_huggingface(self) -> Embeddings:
        from langchain_huggingface import HuggingFaceEmbeddings
        model_name = self.model or "sentence-transformers/all-MiniLM-L6-v2"
        # 国内优先使用 hf-mirror.com 镜像
        mirror_url = "https://hf-mirror.com"
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder="./.hf_cache",
            # 通过环境变量设置镜像
            # export HF_ENDPOINT=https://hf-mirror.com
        )

    def _create_qwen(self) -> Embeddings:
        """千问 DashScope embedding — 通过 OpenAI 兼容接口调用。"""
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=self.model or "text-embedding-v4",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        )

    def _create_custom(self) -> Embeddings:
        """自定义 OpenAI 兼容 embedding 端点。"""
        from langchain_openai import OpenAIEmbeddings
        if not self.base_url:
            raise ValueError("custom embedding 必须提供 base_url")
        return OpenAIEmbeddings(
            model=self.model or "text-embedding-ada-002",
            base_url=self.base_url,
            api_key=self.api_key or "not-needed",
        )
