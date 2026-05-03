from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mega AI Face Stream"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/mega_ai"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
