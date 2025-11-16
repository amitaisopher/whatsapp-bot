"""Worker task implementations."""
import asyncio
from datetime import timedelta
from typing import Optional, Dict, Any

from arq import Retry
from httpx import AsyncClient

from app.services.whatsapp import WhatsAppService
from app.services.inventory_search import (
    NLInventorySearchService,
    get_inventory_search_service,
)
from app.workers.job_deduplication import (
    is_job_already_processed,
    mark_job_as_processed,
)
from app.workers.error_handling import (
    log_job_failure,
    move_to_dead_letter_queue,
    get_retry_delay,
)


async def download_content(ctx: dict[str, Any], url: str) -> str:
    """
    Download content from URL with retry logic.
    
    Args:
        ctx: Worker context
        url: URL to download from
    
    Returns:
        Success message
        
    Raises:
        Retry: To retry the job after a delay
    """
    logger = ctx["logger"]
    job_info = ctx.get("job_try", 1)
    max_tries = 3

    # Create unique job key
    job_key = f"download:{hash(url)}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"Job {job_key} already processed, skipping")
        return f"Already downloaded content from {url}"

    try:
        logger.info(f"Downloading content from {url} (attempt {job_info})")
        await asyncio.sleep(5)  # Simulate network delay
        result = f"Downloaded content from {url}"

        # Mark as processed on success
        await mark_job_as_processed(ctx, job_key)
        logger.info(f"Successfully completed job {job_key}")
        return result

    except Exception as e:
        # Log the failure
        await log_job_failure(
            ctx,
            job_key,
            e,
            job_info,
            max_tries,
            url=url,
            function="download_content",
        )
        
        if job_info < max_tries:
            # Calculate retry delay
            retry_delay = await get_retry_delay(job_info)
            logger.info(f"Retrying job {job_key} after {retry_delay}s")
            
            # Raise Retry exception to tell ARQ to retry
            raise Retry(defer=timedelta(seconds=retry_delay))
        else:
            # Move to dead letter queue
            await move_to_dead_letter_queue(
                ctx,
                job_key,
                e,
                url=url,
                function="download_content",
            )
            
            # Re-raise to mark job as failed
            raise


async def handle_incoming_whatsapp_message(
    ctx: dict[str, Any],
    customer_id: str,
    from_number: str,
    user_message: str,
    message_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Process incoming WhatsApp message with retry logic.
    
    Args:
        ctx: Worker context
        customer_id: Customer UUID
        from_number: Sender's phone number
        user_message: Message content
        message_id: Optional WhatsApp message ID
    
    Returns:
        Processing result dict
        
    Raises:
        Retry: To retry the job after a delay
    """
    logger = ctx["logger"]
    whatsapp_service: WhatsAppService = ctx["whatsapp_service"]
    session: AsyncClient = ctx["session"]
    job_info = ctx.get("job_try", 1)
    max_tries = 3

    # Create unique job key using message_id or hash of parameters
    job_key = message_id or f"whatsapp:{hash((customer_id, from_number, user_message))}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"WhatsApp message {job_key} already processed, skipping")
        return {"status": "already_processed", "job_key": job_key}
        
    try:
        inventory_search_service: NLInventorySearchService = (
            get_inventory_search_service(customer_id, session)
        )

        logger.info(
            f"Processing WhatsApp message {job_key} from {from_number} (attempt {job_info})"
        )

        # Process the message
        response = await inventory_search_service.process_message(
            user_message, from_number
        )

        if response:
            message_to_send: str = response.get("reply", "No response available")

            # Send the response
            send_result = await whatsapp_service.send_message(
                from_number, message_to_send
            )

            if send_result:
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
        # Log the failure with context
        await log_job_failure(
            ctx,
            job_key,
            e,
            job_info,
            max_tries,
            customer_id=customer_id,
            from_number=from_number,
            user_message=user_message[:100],  # Truncate for logging
            function="handle_incoming_whatsapp_message",
        )
        
        if job_info < max_tries:
            # Calculate retry delay
            retry_delay = await get_retry_delay(job_info)
            logger.info(f"Retrying job {job_key} after {retry_delay}s")
            
            # Raise Retry exception to tell ARQ to retry
            raise Retry(defer=timedelta(seconds=retry_delay))
        else:
            # Move to dead letter queue
            await move_to_dead_letter_queue(
                ctx,
                job_key,
                e,
                customer_id=customer_id,
                from_number=from_number,
                user_message=user_message,
                function="handle_incoming_whatsapp_message",
            )
            
            # Don't re-raise - return error status instead
            # This prevents the job from being marked as failed and allows graceful degradation
            return {
                "status": "dead_letter",
                "job_key": job_key,
                "error": str(e),
            }


async def send_whatsapp_message(
    ctx: dict[str, Any],
    to: str,
    content: str,
    message_id: Optional[str] = None,
) -> str:
    """
    Send WhatsApp message with retry logic.
    
    Args:
        ctx: Worker context
        to: Recipient phone number
        content: Message content
        message_id: Optional message ID for deduplication
    
    Returns:
        Success message
        
    Raises:
        Retry: To retry the job after a delay
    """
    logger = ctx["logger"]
    whatsapp_service: WhatsAppService = ctx["whatsapp_service"]
    job_info = ctx.get("job_try", 1)
    max_tries = 3

    # Create unique job key
    job_key = message_id or f"send:{hash((to, content))}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"WhatsApp send job {job_key} already processed, skipping")
        return f"Already sent WhatsApp message to {to}"

    try:
        logger.info(f"Sending WhatsApp message {job_key} to {to} (attempt {job_info})")
        
        result = await whatsapp_service.send_message(to, content)

        if result:
            await mark_job_as_processed(ctx, job_key)
            logger.info(f"Successfully sent WhatsApp message {job_key} to {to}")
            return f"Sent WhatsApp message to {to}"
        else:
            logger.error(f"Failed to send WhatsApp message {job_key}: {result}")
            raise Exception(f"Failed to send message: {result}")

    except Exception as e:
        # Log the failure
        await log_job_failure(
            ctx,
            job_key,
            e,
            job_info,
            max_tries,
            to=to,
            content=content[:100],  # Truncate for logging
            function="send_whatsapp_message",
        )
        
        if job_info < max_tries:
            # Calculate retry delay
            retry_delay = await get_retry_delay(job_info)
            logger.info(f"Retrying job {job_key} after {retry_delay}s")
            
            # Raise Retry exception to tell ARQ to retry
            raise Retry(defer=timedelta(seconds=retry_delay))
        else:
            # Move to dead letter queue
            await move_to_dead_letter_queue(
                ctx,
                job_key,
                e,
                to=to,
                content=content,
                function="send_whatsapp_message",
            )
            
            # Re-raise to mark job as failed
            raise
