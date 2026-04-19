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


settings = Settings()  # type: ignore[call-arg]
