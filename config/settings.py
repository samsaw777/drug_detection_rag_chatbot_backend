from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    All application settings loaded from .env file.
    Never hardcode secrets or config values directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GEMINI_API_KEY: str = "my_api_key"

    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: str = ""
    LANGCHAIN_PROJECT: str = ""
    LANGCHAIN_ENDPOINT: str = ""
    # ── App ──
    APP_NAME: str = "APDP"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — reads .env once."""
    return Settings()