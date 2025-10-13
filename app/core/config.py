from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Literal

EnvironmentType = Literal["development", "production", "testing"]


class Settings(BaseSettings):
    """Application configuration settings."""

    app_name: str = Field(default="WhatsApp Chatbot", alias="APP_NAME")
    environment: EnvironmentType = Field(
        default="development",
    )
    upstash_redis_rest_url: str | None = Field(default=None, alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str | None = Field(default=None, alias="UPSTASH_REDIS_REST_TOKEN")
    upstash_redis_host: str = Field(default="localhost", alias="UPSTASH_REDIS_HOST")
    upstash_redis_port: int = Field(default=6379, alias="UPSTASH_REDIS_PORT")
    upstash_redis_password: str | None = Field(default=None, alias="UPSTASH_REDIS_PASSWORD")

    # WhatsApp config
    whatsapp_access_token: str | None = Field(default=None, alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_webhook_verification_token: str | None = Field(default=None, alias="WHATSAPP_WEBHOOK_VERIFICATION_TOKEN")
    whatsapp_app_secret: str | None = Field(default=None, alias="WHATSAPP_APP_SECRET")
    whatsapp_app_id: str | None = Field(default=None, alias="WHATSAPP_APP_ID")
    whatsapp_recipient_waid: str | None = Field(default=None, alias="WHATSAPP_RECIPIENT_WAID")
    whatsapp_api_version: str | None = Field(default=None, alias="WHATSAPP_API_VERSION")
    whatsapp_phone_number_id: str | None = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")

    # Sentry config
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    sentry_enabled: bool = Field(default=False, alias="SENTRY_ENABLED")
    inventory_assitant_url: str   = Field(
        default="http://localhost:8001", alias="INVENTORY_ASSISTANT_URL"
    )
    api_key: str | None = Field(default=None, alias="API_KEY")
    debug: bool = Field(default=True, alias="DEBUG")

    @property
    def upstash_redis_url(self) -> str | None:
        """Construct the Upstash Redis URL if host and password are provided."""
        if self.upstash_redis_host and self.upstash_redis_password:
            return f"rediss://default:{self.upstash_redis_password}@{self.upstash_redis_host}:{self.upstash_redis_port}"
        return None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


@lru_cache
def get_settings():
    return Settings()


settings: Settings = Settings()
