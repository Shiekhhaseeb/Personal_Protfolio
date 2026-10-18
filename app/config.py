from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "production"] = "development"
    environment: Literal["development", "production"] | None = None
    trusted_proxy_count: int = 1
    log_level: str = "info"
    llm_provider: Literal["groq", "gemini"] = "groq"
    groq_api_key: str = ""
    google_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    gemini_model: str = "gemini-2.0-flash"
    chat_rate_limit: int = 20
    app_version: str = "1.0.0"

    @property
    def is_production(self) -> bool:
        return (self.environment or self.env) == "production"

    @property
    def chat_enabled(self) -> bool:
        if self.llm_provider == "groq":
            return bool(self.groq_api_key)
        return bool(self.google_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
