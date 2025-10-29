from arq.connections import RedisSettings
from app.core.config import settings, Environment

# Upstash Redis connection (TLS)
REDIS_SETTINGS: RedisSettings = RedisSettings(
    host=settings.upstash_redis_host,
    port=settings.upstash_redis_port,
    password=settings.upstash_redis_password,
    ssl=False if settings.environment == Environment.DEVELOPMENT else True,
)

def get_redis_url() -> str | None:
    """Construct the Upstash Redis URL if host and password are provided."""
    if settings.environment != Environment.DEVELOPMENT:
        return settings.upstash_redis_rest_url or None
    if settings.upstash_redis_host and settings.upstash_redis_password:
        return f"redis://default:{settings.upstash_redis_password}@{settings.upstash_redis_host}:{settings.upstash_redis_port}"
    return None