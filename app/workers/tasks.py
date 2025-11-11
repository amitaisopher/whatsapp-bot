# tasks.py
from httpx import AsyncClient
import asyncio
from typing import Optional, Dict, Any

from app.core.redis import REDIS_SETTINGS
from app.services.whatsapp import get_whatsapp_service, WhatsAppService
from app.services.inventory_search import (
    NLInventorySearchService,
    get_inventory_search_service,
)
from app.core.logging import get_application_logger
from app.core.config import get_settings
from redis.exceptions import AuthenticationError, ConnectionError

settings = get_settings()


# Job deduplication using Redis
async def is_job_already_processed(ctx, job_key: str) -> bool:
    """Check if a job has already been processed successfully."""
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


async def mark_job_as_processed(ctx, job_key: str, ttl: int = 3600) -> None:
    """Mark a job as successfully processed."""
    redis = ctx.get("redis")
    if redis:
        try:
            await redis.setex(f"job_processed:{job_key}", ttl, "1")
        except (AuthenticationError, ConnectionError) as e:
            logger = ctx.get("logger") or get_application_logger()
            logger.error(
                f"Redis error raised during attempt to update job {job_key}: {e}"
            )


async def download_content(ctx, url: str) -> str:
    logger = ctx["logger"]

    # Create unique job key
    job_key = f"download:{hash(url)}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"Job {job_key} already processed, skipping")
        return f"Already downloaded content from {url}"

    try:
        logger.info(f"Downloading content from {url}")
        await asyncio.sleep(5)  # Simulate network delay
        result = f"Downloaded content from {url}"

        # Mark as processed on success
        await mark_job_as_processed(ctx, job_key)
        logger.info(f"Successfully completed job {job_key}")
        return result

    except Exception as e:
        logger.error(f"Failed to download content from {url}: {e}")
        raise  # Re-raise to trigger retry if configured


async def handle_incoming_whatsapp_message(
    ctx,
    customer_id: str,
    from_number: str,
    user_message: str,
    message_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    logger = ctx["logger"]
    whatsapp_service: WhatsAppService = ctx["whatsapp_service"]
    session: AsyncClient = ctx["session"]

    # Create unique job key using message_id or hash of parameters
    job_key = message_id or f"whatsapp:{hash((customer_id, from_number, user_message))}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"WhatsApp message {job_key} already processed, skipping")
        return {"status": "already_processed", "job_key": job_key}
        # Proceed with processing in case of Redis error
    try:
        inventory_search_service: NLInventorySearchService = (
            get_inventory_search_service(customer_id, session)
        )

        logger.info(f"Processing WhatsApp message {job_key} from {from_number}")

        # Process the message
        response = await inventory_search_service.process_message(
            user_message, from_number
        )

        if response:
            message_to_send: str = response.get("response", "No response available")

            # Send the response
            send_result = await whatsapp_service.send_message(
                from_number, message_to_send
            )

            # Note: Assuming send_message returns a dict with success status
            # You may need to adjust this based on your actual WhatsApp service implementation
            if (
                send_result
            ):  # Adjust this condition based on your send_message return format
                # Mark as processed only on successful send
                await mark_job_as_processed(ctx, job_key)
                logger.info(f"Successfully processed WhatsApp message {job_key}")

                return {
                    "status": "success",
                    "job_key": job_key,
                    "message_sent": message_to_send,
                    "send_result": send_result,
                }
            else:
                logger.error(f"Failed to send WhatsApp message for {job_key}")
                raise Exception("Failed to send message")
        else:
            logger.warning(
                f"No response received for message {job_key} from {from_number}"
            )
            # Mark as processed even if no response (to avoid infinite retries)
            await mark_job_as_processed(ctx, job_key)
            return {"status": "no_response", "job_key": job_key}

    except Exception as e:
        logger.error(
            f"Error handling WhatsApp message {job_key} from {from_number}: {e}"
        )
        raise  # Re-raise to trigger retry


async def send_whatsapp_message(
    ctx, to: str, content: str, message_id: Optional[str] = None
) -> str:
    logger = ctx["logger"]
    whatsapp_service: WhatsAppService = ctx["whatsapp_service"]

    # Create unique job key
    job_key = message_id or f"send:{hash((to, content))}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"WhatsApp send job {job_key} already processed, skipping")
        return f"Already sent WhatsApp message to {to}"

    try:
        result = await whatsapp_service.send_message(to, content)

        if result:  # Adjust this condition based on your send_message return format
            await mark_job_as_processed(ctx, job_key)
            logger.info(f"Successfully sent WhatsApp message {job_key} to {to}")
            return f"Sent WhatsApp message to {to}"
        else:
            logger.error(f"Failed to send WhatsApp message {job_key}: {result}")
            raise Exception(f"Failed to send message: {result}")

    except Exception as e:
        logger.error(f"Error sending WhatsApp message {job_key} to {to}: {e}")
        raise


async def startup(ctx):
    logger = get_application_logger()
    ctx["session"] = AsyncClient(timeout=settings.inventory_search_timeout)
    ctx["whatsapp_service"] = get_whatsapp_service()
    ctx["logger"] = logger

    # Add Redis connection for job deduplication
    import redis.asyncio as redis

    logger.info(f"Connecting to Redis host: {settings.redis_host} ")

    ctx["redis"] = redis.from_url(
        url=settings.redis_url,
        decode_responses=True,
    )

    logger.info("Worker startup complete.")


async def shutdown(ctx):
    await ctx["session"].aclose()

    # Close Redis connection
    if "redis" in ctx:
        await ctx["redis"].close()

    logger = ctx["logger"]
    logger.info("Worker shutdown complete.")


# WorkerSettings defines the settings to use when creating the work,
# It's used by the arq CLI.
# redis_settings might be omitted here if using the default settings
# For a list of all available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker


class WorkerSettings:
    functions = [
        download_content,
        send_whatsapp_message,
        handle_incoming_whatsapp_message,
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS

    # Configure job retry and deduplication settings
    max_tries = 3  # Maximum retry attempts
    retry_jobs = True  # Enable job retries
    job_timeout = 300  # Job timeout in seconds (5 minutes)
    keep_result = 3600  # Keep job results for 1 hour

    # Important: Set max_jobs to control concurrent job processing
    max_jobs = 10  # Maximum concurrent jobs per worker
