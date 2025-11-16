"""Job deduplication utilities using Redis."""
from typing import Any

from app.core.logging import get_application_logger
from redis.exceptions import AuthenticationError, ConnectionError


async def is_job_already_processed(ctx: dict[str, Any], job_key: str) -> bool:
    """
    Check if a job has already been processed successfully.
    
    Args:
        ctx: Worker context containing Redis connection
        job_key: Unique job identifier
    
    Returns:
        True if job was already processed, False otherwise
    """
    redis = ctx.get("redis")
    if redis:
        try:
            result = await redis.get(f"job_processed:{job_key}")
            return result is not None
        except (AuthenticationError, ConnectionError) as e:
            logger = ctx.get("logger") or get_application_logger()
            logger.error(f"Redis error while checking job {job_key}: {e}")
            # In case of Redis error, we choose to proceed with processing
    return False


async def mark_job_as_processed(ctx: dict[str, Any], job_key: str, ttl: int = 3600) -> None:
    """
    Mark a job as successfully processed.
    
    Args:
        ctx: Worker context containing Redis connection
        job_key: Unique job identifier
        ttl: Time-to-live in seconds (default: 1 hour)
    """
    redis = ctx.get("redis")
    if redis:
        try:
            await redis.setex(f"job_processed:{job_key}", ttl, "1")
        except (AuthenticationError, ConnectionError) as e:
            logger = ctx.get("logger") or get_application_logger()
            logger.error(
                f"Redis error raised during attempt to update job {job_key}: {e}"
            )
