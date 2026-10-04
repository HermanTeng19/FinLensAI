from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "FinLens AI Backend"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://finlens_user:finlens_password@localhost:5432/finlens_db"

    # CORS configuration
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
