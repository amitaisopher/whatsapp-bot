from arq.connections import RedisSettings
from app.core.config import settings

# Upstash Redis connection (TLS)
REDIS_SETTINGS: RedisSettings = RedisSettings(
  host=settings.upstash_redis_host,
  port=settings.upstash_redis_port,
  password=settings.upstash_redis_password,
  ssl=True,
)