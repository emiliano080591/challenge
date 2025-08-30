from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = "sqlite+pysqlite:///./local.db"

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 350

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
