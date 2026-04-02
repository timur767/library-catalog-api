from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Library Catalog API"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    database_url: PostgresDsn
    database_pool_size: int = 20
    api_v1_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    cors_origins: list[str] = []
    openlibrary_base_url: str = "https://openlibrary.org"
    openlibrary_timeout: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def database_url_str(self) -> str:
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
