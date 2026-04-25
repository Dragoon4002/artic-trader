"""App configuration via pydantic-settings."""
from typing import Optional

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    # Hub connection (injected by hub at spawn)
    HUB_URL: str = ""
    HUB_AGENT_ID: str = ""
    INTERNAL_SECRET: str = ""

    # Trading config defaults — overridden by /start body
    SYMBOL: str = "BTCUSDT"
    AMOUNT_USDT: float = 100.0
    LEVERAGE: int = 5

    # API keys
    TWELVE_DATA_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    CMC_API_KEY: str = ""

    # Exchange (live mode)
    HASHKEY_API_KEY: str = ""
    HASHKEY_SECRET: str = ""

    # Optional MongoDB cache
    MONGODB_URI: str = ""

    # On-chain (Initia rollup; CHAIN_*/HSK_* kept as fallback aliases)
    INITIA_RPC_URL: str = ""
    INITIA_PRIVATE_KEY: str = ""
    INITIA_CHAIN_ID: str = ""
    INITIA_EXPLORER_BASE: str = "https://scan.testnet.initia.xyz"
    CHAIN_RPC_URL: str = ""
    CHAIN_PRIVATE_KEY: str = ""
    HSK_RPC_URL: str = ""
    HSK_PRIVATE_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = AppSettings()
