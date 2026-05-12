from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite+aiosqlite:///./eventlens.db"
    DATABASE_URL_SYNC: str = "sqlite:///./eventlens.db"
    REDIS_URL: str = ""  # empty = skip Redis cache
    CELERY_BROKER_URL: str = ""

    QWEN_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    MOCK_LLM_ENABLED: bool = True
    LLM_PROVIDER: str = "mock"

    SEED_ON_STARTUP: bool = False

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()