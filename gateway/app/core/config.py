from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for API Gateway."""
    SERVICE_NAME: str = "api-gateway"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # NATS Configuration
    NATS_URL: str = "nats://nats:4222"
    NATS_USER: str | None = "app_user"
    NATS_PASSWORD: str | None = "nats_secret_password"
    NATS_REQUEST_TIMEOUT_SECONDS: float = 5.0

    # JWT Authentication
    JWT_SECRET: str = "super-secret-jwt-key-replace-in-production-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
