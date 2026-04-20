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

    # Wallet auth
    AUTH_MESSAGE_DOMAIN: str = "artic.trade"
    AUTH_NONCE_TTL_SECONDS: int = 300
    AUTH_SESSION_TTL_SECONDS: int = 28800  # 8h
    AUTH_SUPPORTED_CHAINS: str = "initia-testnet"  # comma-separated

    # Initia .init name service
    INITIA_NAME_SERVICE_URL: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
