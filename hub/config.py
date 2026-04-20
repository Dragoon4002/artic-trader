"""Hub configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    DATABASE_URL: str = ""  # postgresql+asyncpg://...
    ENV: str = "dev"  # dev | staging | prod
    HUB_PORT: int = 8000

    # Auth / secrets
    JWT_SECRET: str = "changeme-jwt"
    JWT_EXPIRY_MINUTES: int = 15
    REFRESH_EXPIRY_DAYS: int = 30
    KEK: str = ""  # 32-byte base64; required in prod
    INTERNAL_SECRET: str = "changeme"  # shared with user-server (legacy name)

    # mTLS
    HUB_CA_KEY_PATH: str = ""  # PEM file on disk; dev generates self-signed
    HUB_CA_CERT_PATH: str = ""

    # VM provider
    VM_PROVIDER: str = "morph"  # morph | firecracker
    VM_PROVIDER_TOKEN: str = ""
    VM_IMAGE_TAG: str = "v0"  # local docker tag on images baked into golden snapshot
    HUB_PUBLIC_URL: str = ""  # reachable from Morph VM; used by golden build + user-server callbacks
    MORPH_API_KEY: str = ""
    MORPH_BASE_URL: str = "https://cloud.morph.so/api"
    BASE_SNAPSHOT_ID: str = ""
    MORPH_GOLDEN_SNAPSHOT_ID: str = ""

    # Market
    TWELVE_DATA_API_KEY: str = ""
    PYTH_HERMES_URL: str = "https://hermes.pyth.network"
    CANDLE_STALENESS_SECONDS: int = 60
    PRICE_POLL_SECONDS: float = 2.0

    # Proxy
    PROXY_CONNECT_TIMEOUT_SECONDS: float = 5.0
    PROXY_READ_TIMEOUT_SECONDS: float = 10.0
    VM_WAKE_TIMEOUT_SECONDS: float = 10.0

    # Chain / funder (stubbed this branch)
    HSK_RPC_URL: str = ""
    PLATFORM_WALLET_KEY: str = ""
    FUND_FLOOR_WEI: int = 0
    FUND_TOPUP_WEI: int = 0
    FUND_INTERVAL_SEC: int = 18000

    # OTel
    OTEL_COLLECTOR_URL: str = ""

    # Wallet auth
    AUTH_MESSAGE_DOMAIN: str = "artic.trade"
    AUTH_NONCE_TTL_SECONDS: int = 300
    AUTH_SESSION_TTL_SECONDS: int = 28800  # 8h
    AUTH_SUPPORTED_CHAINS: str = "initia-testnet"  # comma-separated

    # Initia .init name service
    INITIA_NAME_SERVICE_URL: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
