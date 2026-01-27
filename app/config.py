"""Configuration management using environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    WEBHOOK_SECRET: str
    DATABASE_URL: str = "sqlite+aiosqlite:////data/app.db"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
