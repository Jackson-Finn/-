from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Advanced Marketplace API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"
    secret_key: str = "advanced-marketplace-dev-secret-key-2026"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./data/advanced_marketplace.db"
    redis_url: str = "redis://redis:6379/0"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "market-assets"
    minio_secure: bool = False
    storage_backend: str = "local"
    media_storage_dir: str = "./storage/uploads"
    media_public_base_url: str = "http://localhost:8000"
    opensearch_url: str = "http://opensearch:9200"
    opensearch_index: str = "products"
    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = "qwen3.5-plus"
    cors_origins: str = "http://localhost:5173,http://localhost"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "Admin123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        return normalized in {"1", "true", "yes", "on", "debug", "development"}

    @field_validator("minio_secure", mode="before")
    @classmethod
    def parse_minio_secure(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        return normalized in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
