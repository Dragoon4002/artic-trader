"""Hub configuration via pydantic-settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""  # must set via .env (postgresql+asyncpg://...)
    INTERNAL_SECRET: str = "changeme"
    JWT_SECRET: str = "changeme-jwt"
    JWT_EXPIRY_MINUTES: int = 15
    TWELVE_DATA_API_KEY: str = ""
    CANDLE_STALENESS_SECONDS: int = 60
    PRICE_POLL_SECONDS: float = 2.0
    HUB_PORT: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
