import os
from enum import StrEnum
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Enum for application environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"


class Settings(BaseSettings):
    """Application configuration settings."""

    def __init__(self, **data):
        super().__init__(**data)

    app_name: str = Field(default="WhatsApp Chatbot", alias="APP_NAME")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
   
    # Redis config
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    @field_validator("redis_port", mode="before")
    @classmethod
    def validate_redis_port(cls, v: Any) -> int:
        """Validate and convert REDIS_PORT to integer, handling empty strings."""
        if v == "" or v is None:
            return 6379  # Return default value
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 6379  # Return default value if conversion fails
        return 6379

    # WhatsApp config
    whatsapp_access_token: str | None = Field(
        default=None, alias="WHATSAPP_ACCESS_TOKEN"
    )
    whatsapp_webhook_verification_token: str | None = Field(
        default=None, alias="WHATSAPP_WEBHOOK_VERIFICATION_TOKEN"
    )
    whatsapp_app_secret: str | None = Field(default=None, alias="WHATSAPP_APP_SECRET")
    whatsapp_app_id: str | None = Field(default=None, alias="WHATSAPP_APP_ID")
    whatsapp_recipient_waid: str | None = Field(
        default=None, alias="WHATSAPP_RECIPIENT_WAID"
    )
    whatsapp_api_version: str | None = Field(default=None, alias="WHATSAPP_API_VERSION")
    whatsapp_phone_number_id: str | None = Field(
        default=None, alias="WHATSAPP_PHONE_NUMBER_ID"
    )

    # Sentry config
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    sentry_enabled: bool = Field(default=False, alias="SENTRY_ENABLED")
    inventory_assitant_url: str = Field(
        default="http://localhost:8001", alias="INVENTORY_ASSISTANT_URL"
    )
    api_key: str | None = Field(default=None, alias="API_KEY")
    debug: bool = Field(default=True, alias="DEBUG")

    # SUPABASE config
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, alias="SUPABASE_KEY")

    # Inventory Search API config
    search_api_url: str | None = Field(default=None, alias="SEARCH_API_URL")

    # Inventory Search timeout
    inventory_search_timeout: int = Field(default=40, alias="INVENTORY_SEARCH_TIMEOUT")

    @property
    def redis_url(self) -> str:
        """Construct the Redis URL if host and password are provided. For production use rediss."""
        if not self.redis_host or not self.redis_password:
            raise ValueError("Redis host or password is not configured")
        if self.environment == Environment.DEVELOPMENT:
            return f"redis://default:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        else:
            return f"rediss://default:{self.redis_password}@{self.redis_host}:{self.redis_port}"

    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="allow")


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings.

    This function reads the ENVIRONMENT environment variable to determine which .env file to load.
    It defaults to 'development' if ENVIRONMENT is not set.
    """
    app_env: str = os.getenv("ENVIRONMENT", Environment.DEVELOPMENT.value)
    env_file = f".env.{app_env}"
    return Settings(_env_file=env_file)


# Module-level settings instance for convenience
settings = get_settings()
