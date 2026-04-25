from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = ""
    HUB_URL: str = ""
    USER_ID: str = ""
    USER_TOKEN: str = ""

    # Auth — hub->us (bearer) and us<->agent (bearer). Rotated on wake in prod.
    HUB_SECRET: str = ""
    INTERNAL_SECRET: str = ""

    # Agent spawner
    AGENT_IMAGE: str = "artic-app:dev"
    AGENT_NETWORK: str = "artic-dev"
    DOCKER_HOST: str = ""  # empty -> docker SDK uses /var/run/docker.sock
    USER_SERVER_INTERNAL_URL: str = "http://host.docker.internal:8000"

    # Chain signing
    CHAIN_RPC_URL: str = ""
    CHAIN_ID: int = 0
    KEYSTORE_PATH: str = ""  # path to encrypted JSON keystore on VM rootfs
    WALLET_PRIVATE_KEY: str = ""  # dev-only plaintext fallback; prod uses KEYSTORE_PATH + KEK
    CONTRACTS_PATH: str = "contracts/deployed.json"


settings = Settings()  # type: ignore[call-arg]
