"""Error handling and retry logic for worker jobs."""
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_application_logger
from app.workers.job_status import JobStatus


async def log_job_failure(
    ctx: dict[str, Any],
    job_key: str,
    error: Exception,
    attempt: int,
    max_attempts: int,
    **job_details,
) -> None:
    """
    Log job failure with detailed context.
    
    Args:
        ctx: Worker context
        job_key: Unique job identifier
        error: The exception that caused the failure
        attempt: Current attempt number
        max_attempts: Maximum number of attempts allowed
        **job_details: Additional job-specific details to log
    """
    logger = ctx.get("logger") or get_application_logger()
    
    error_details = {
        "job_key": job_key,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "attempt": attempt,
        "max_attempts": max_attempts,
        "status": JobStatus.RETRY if attempt < max_attempts else JobStatus.DEAD_LETTER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **job_details,
    }
    
    if attempt < max_attempts:
        logger.warning(
            f"Job {job_key} failed (attempt {attempt}/{max_attempts}), will retry",
            extra=error_details,
        )
    else:
        logger.error(
            f"Job {job_key} failed after {max_attempts} attempts, moving to dead letter queue",
            extra=error_details,
        )


async def move_to_dead_letter_queue(
    ctx: dict[str, Any],
    job_key: str,
    error: Exception,
    **job_details,
) -> None:
    """
    Move failed job to dead letter queue for manual review.
    
    Args:
        ctx: Worker context
        job_key: Unique job identifier
        error: The exception that caused the final failure
        **job_details: Job data for future retry/investigation
    """
    redis = ctx.get("redis")
    logger = ctx.get("logger") or get_application_logger()
    
    if not redis:
        logger.error(f"Cannot move job {job_key} to DLQ: Redis not available")
        return
    
    try:
        dlq_entry = {
            "job_key": job_key,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_details": str(job_details),
        }
        
        # Store in Redis hash for easy retrieval and management
        await redis.hset(
            f"dlq:{job_key}",
            mapping={
                k: str(v) for k, v in dlq_entry.items()
            }
        )
        
        # Add to DLQ list for processing
        await redis.lpush("dead_letter_queue", job_key)
        
        # Set expiry (keep for 7 days)
        await redis.expire(f"dlq:{job_key}", 7 * 24 * 3600)
        
        logger.error(
            f"Job {job_key} moved to dead letter queue",
            extra=dlq_entry,
        )
        
    except Exception as e:
        logger.error(f"Failed to move job {job_key} to DLQ: {e}")


async def get_retry_delay(attempt: int) -> int:
    """
    Calculate exponential backoff delay for retries.
    
    Args:
        attempt: Current attempt number (1-indexed)
    
    Returns:
        Delay in seconds
    """
    # Exponential backoff: 30s, 60s, 120s, 240s, etc.
    # Capped at 10 minutes
    base_delay = 30
    max_delay = 600
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    return delay
