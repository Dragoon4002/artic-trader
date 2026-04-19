from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    HUB_URL: str
    USER_ID: str
    USER_TOKEN: str


settings = Settings()  # type: ignore[call-arg]
