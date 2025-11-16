"""Worker lifecycle management (startup and shutdown)."""
from typing import Any

import redis.asyncio as redis
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.logging import get_application_logger
from app.services.whatsapp import get_whatsapp_service


settings = get_settings()


async def startup(ctx: dict[str, Any]) -> None:
    """
    Initialize worker context with necessary services and connections.
    
    Args:
        ctx: Worker context dictionary to populate
    """
    logger = get_application_logger()
    
    # Initialize HTTP client with timeout
    ctx["session"] = AsyncClient(timeout=settings.inventory_search_timeout)
    
    # Initialize WhatsApp service
    ctx["whatsapp_service"] = get_whatsapp_service()
    
    # Initialize logger
    ctx["logger"] = logger

    # Initialize Redis connection for job deduplication
    logger.info(f"Connecting to Redis host: {settings.redis_host}")
    ctx["redis"] = redis.from_url(
        url=settings.redis_url,
        decode_responses=True,
    )

    logger.info("Worker startup complete.")


async def shutdown(ctx: dict[str, Any]) -> None:
    """
    Clean up worker resources on shutdown.
    
    Args:
        ctx: Worker context dictionary with resources to clean up
    """
    logger = ctx["logger"]
    
    # Close HTTP client
    await ctx["session"].aclose()

    # Close Redis connection
    if "redis" in ctx:
        await ctx["redis"].aclose()

    logger.info("Worker shutdown complete.")
