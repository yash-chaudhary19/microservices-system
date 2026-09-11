from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for User Service."""
    SERVICE_NAME: str = "user-service"
    PORT: int = 8001
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/users_db"

    # NATS Configuration
    NATS_URL: str = "nats://nats:4222"
    NATS_USER: str | None = "app_user"
    NATS_PASSWORD: str | None = "nats_secret_password"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
