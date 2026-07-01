"""Pydantic BaseSettings — 从 .env 和环境变量加载全局配置。"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，自动从 .env 文件和环境变量加载。"""

    # API Keys
    anthropic_api_key: str = ""
    dashscope_api_key: str = ""   # 通义千问
    deepseek_api_key: str = ""    # DeepSeek

    # Embedding
    embedding_provider: str = "openai"  # "openai" | "huggingface" | "custom"
    embedding_model: str = "text-embedding-3-small"

    # 存储路径
    chroma_persist_dir: str = "./chroma_db"
    user_data_dir: str = "./user_data"

    # 日志
    log_level: str = "INFO"

    # 默认模型
    default_provider: str = "qwen"
    default_model: str = "qwen-plus-latest"
    default_temperature: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def ensure_dirs(self) -> None:
        """确保必要的目录存在。"""
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)


# 全局单例
settings = Settings()
