from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for Notification Service."""
    SERVICE_NAME: str = "notification-service"
    PORT: int = 8002
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/notifications_db"

    # NATS Configuration
    NATS_URL: str = "nats://nats:4222"
    NATS_USER: str | None = "app_user"
    NATS_PASSWORD: str | None = "nats_secret_password"

    # JetStream Consumer Configuration
    CONSUMER_ACK_WAIT_SECONDS: int = 10
    CONSUMER_MAX_DELIVER: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
