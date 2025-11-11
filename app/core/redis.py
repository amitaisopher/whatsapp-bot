from arq.connections import RedisSettings
from app.core.config import settings, Environment

# Upstash Redis connection (TLS)
REDIS_SETTINGS: RedisSettings = RedisSettings(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    ssl=False if settings.environment == Environment.DEVELOPMENT else True,
)
