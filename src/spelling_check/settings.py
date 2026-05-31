from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPELLING_", extra="ignore")

    base_url: str = "http://localhost:7072/v1"
    model: str = "gemma-4-26b-a4b"
    api_key: str | None = None
    timeout: float = 30.0
    web_host: str = "127.0.0.1"
    web_port: int = 8000

    @property
    def normalized_api_key(self) -> str | None:
        if self.api_key is None:
            return None
        api_key = self.api_key.strip()
        return api_key or None


def load_env_settings() -> EnvironmentSettings:
    return EnvironmentSettings()
