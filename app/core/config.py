from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = "sqlite+pysqlite:///./local.db"

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
