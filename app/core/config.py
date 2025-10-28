import os
from enum import StrEnum
from functools import lru_cache

from pydantic import Field
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
    upstash_redis_rest_url: str | None = Field(
        default=None, alias="UPSTASH_REDIS_REST_URL"
    )
    upstash_redis_rest_token: str | None = Field(
        default=None, alias="UPSTASH_REDIS_REST_TOKEN"
    )
    upstash_redis_host: str = Field(
        default="localhost", alias="UPSTASH_REDIS_HOST")
    upstash_redis_port: int = Field(default=6379, alias="UPSTASH_REDIS_PORT")
    upstash_redis_password: str | None = Field(
        default=None, alias="UPSTASH_REDIS_PASSWORD"
    )

    # WhatsApp config
    whatsapp_access_token: str | None = Field(
        default=None, alias="WHATSAPP_ACCESS_TOKEN"
    )
    whatsapp_webhook_verification_token: str | None = Field(
        default=None, alias="WHATSAPP_WEBHOOK_VERIFICATION_TOKEN"
    )
    whatsapp_app_secret: str | None = Field(
        default=None, alias="WHATSAPP_APP_SECRET")
    whatsapp_app_id: str | None = Field(default=None, alias="WHATSAPP_APP_ID")
    whatsapp_recipient_waid: str | None = Field(
        default=None, alias="WHATSAPP_RECIPIENT_WAID"
    )
    whatsapp_api_version: str | None = Field(
        default=None, alias="WHATSAPP_API_VERSION")
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

    # Search API config
    search_api_url: str | None = Field(default=None, alias="SEARCH_API_URL")

    @property
    def upstash_redis_url(self) -> str | None:
        """Construct the Upstash Redis URL if host and password are provided."""
        if self.upstash_redis_host and self.upstash_redis_password:
            return f"rediss://default:{self.upstash_redis_password}@{self.upstash_redis_host}:{self.upstash_redis_port}"
        return None

    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """
    Get the application settings.

    This function reads the APP_ENV environment variable to determine which .env file to load.
    It defaults to 'development' if APP_ENV is not set.
    """
    app_env: str = os.getenv("APP_ENV", Environment.DEVELOPMENT.value)
    env_file = f".env.{app_env}"
    return Settings(_env_file=env_file)


settings: Settings = get_settings()
