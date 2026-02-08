from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./pat.db"
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "PAT_"}


settings = Settings()
