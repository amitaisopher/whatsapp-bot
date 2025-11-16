"""Test worker error handling and retry logic."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import timedelta

from arq import Retry

from app.workers.task_functions import (
    download_content,
    handle_incoming_whatsapp_message,
    send_whatsapp_message,
)
from app.workers.error_handling import (
    get_retry_delay,
    log_job_failure,
    move_to_dead_letter_queue,
)
from app.workers.job_deduplication import (
    is_job_already_processed,
    mark_job_as_processed,
)


@pytest.mark.asyncio
async def test_get_retry_delay():
    """Test exponential backoff calculation."""
    assert await get_retry_delay(1) == 30  # 30s
    assert await get_retry_delay(2) == 60  # 60s
    assert await get_retry_delay(3) == 120  # 120s
    assert await get_retry_delay(4) == 240  # 240s
    assert await get_retry_delay(10) == 600  # Capped at 600s


@pytest.mark.asyncio
async def test_is_job_already_processed_true():
    """Test checking if job is already processed - returns True."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = "1"
    
    ctx = {"redis": redis_mock, "logger": Mock()}
    result = await is_job_already_processed(ctx, "test_job_key")
    
    assert result is True
    redis_mock.get.assert_called_once_with("job_processed:test_job_key")


@pytest.mark.asyncio
async def test_is_job_already_processed_false():
    """Test checking if job is already processed - returns False."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    ctx = {"redis": redis_mock, "logger": Mock()}
    result = await is_job_already_processed(ctx, "test_job_key")
    
    assert result is False


@pytest.mark.asyncio
async def test_mark_job_as_processed():
    """Test marking job as processed."""
    redis_mock = AsyncMock()
    ctx = {"redis": redis_mock, "logger": Mock()}
    
    await mark_job_as_processed(ctx, "test_job_key", ttl=1800)
    
    redis_mock.setex.assert_called_once_with("job_processed:test_job_key", 1800, "1")


@pytest.mark.asyncio
async def test_log_job_failure_retry():
    """Test logging job failure when retrying."""
    logger_mock = Mock()
    ctx = {"logger": logger_mock}
    error = Exception("Test error")
    
    await log_job_failure(
        ctx,
        "test_job_key",
        error,
        attempt=1,
        max_attempts=3,
        customer_id="test-customer",
    )
    
    # Should log warning for retry
    assert logger_mock.warning.called


@pytest.mark.asyncio
async def test_log_job_failure_dead_letter():
    """Test logging job failure when moving to DLQ."""
    logger_mock = Mock()
    ctx = {"logger": logger_mock}
    error = Exception("Test error")
    
    await log_job_failure(
        ctx,
        "test_job_key",
        error,
        attempt=3,
        max_attempts=3,
        customer_id="test-customer",
    )
    
    # Should log error for DLQ
    assert logger_mock.error.called


@pytest.mark.asyncio
async def test_move_to_dead_letter_queue():
    """Test moving job to dead letter queue."""
    redis_mock = AsyncMock()
    logger_mock = Mock()
    ctx = {"redis": redis_mock, "logger": logger_mock}
    error = Exception("Test error")
    
    await move_to_dead_letter_queue(
        ctx,
        "test_job_key",
        error,
        customer_id="test-customer",
        function="test_function",
    )
    
    # Should store in hash and add to list
    assert redis_mock.hset.called
    assert redis_mock.lpush.called
    assert redis_mock.expire.called


@pytest.mark.asyncio
async def test_download_content_already_processed():
    """Test download_content when job is already processed."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = "1"  # Already processed
    
    logger_mock = Mock()
    ctx = {"redis": redis_mock, "logger": logger_mock}
    
    result = await download_content(ctx, "https://example.com")
    
    assert "Already downloaded" in result
    logger_mock.info.assert_called()


@pytest.mark.asyncio
async def test_download_content_retry_on_failure():
    """Test download_content retries on failure."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    logger_mock = Mock()
    ctx = {"redis": redis_mock, "logger": logger_mock, "job_try": 1}
    
    # Mock sleep to raise exception
    with patch("asyncio.sleep", side_effect=Exception("Network error")):
        with pytest.raises(Retry):
            await download_content(ctx, "https://example.com")


@pytest.mark.asyncio
async def test_send_whatsapp_message_success():
    """Test send_whatsapp_message successful send."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    whatsapp_mock = AsyncMock()
    whatsapp_mock.send_message.return_value = {"success": True}
    
    logger_mock = Mock()
    ctx = {
        "redis": redis_mock,
        "logger": logger_mock,
        "whatsapp_service": whatsapp_mock,
        "job_try": 1,
    }
    
    result = await send_whatsapp_message(ctx, "+1234567890", "Test message")
    
    assert "Sent WhatsApp message" in result
    redis_mock.setex.assert_called()  # Should mark as processed


@pytest.mark.asyncio
async def test_send_whatsapp_message_retry():
    """Test send_whatsapp_message retries on failure."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    whatsapp_mock = AsyncMock()
    whatsapp_mock.send_message.side_effect = Exception("API error")
    
    logger_mock = Mock()
    ctx = {
        "redis": redis_mock,
        "logger": logger_mock,
        "whatsapp_service": whatsapp_mock,
        "job_try": 1,
    }
    
    with pytest.raises(Retry):
        await send_whatsapp_message(ctx, "+1234567890", "Test message")


@pytest.mark.asyncio
async def test_handle_incoming_whatsapp_message_success():
    """Test handle_incoming_whatsapp_message successful processing."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    whatsapp_mock = AsyncMock()
    whatsapp_mock.send_message.return_value = {"success": True}
    
    session_mock = AsyncMock()
    
    logger_mock = Mock()
    ctx = {
        "redis": redis_mock,
        "logger": logger_mock,
        "whatsapp_service": whatsapp_mock,
        "session": session_mock,
        "job_try": 1,
    }
    
    with patch("app.workers.task_functions.get_inventory_search_service") as mock_service:
        service_instance = AsyncMock()
        service_instance.process_message.return_value = {"reply": "Test reply"}
        mock_service.return_value = service_instance
        
        result = await handle_incoming_whatsapp_message(
            ctx,
            "customer-123",
            "+1234567890",
            "Hello",
            "msg-123",
        )
        
        assert result["status"] == "success"
        assert "message_sent" in result


@pytest.mark.asyncio
async def test_handle_incoming_whatsapp_message_dead_letter():
    """Test handle_incoming_whatsapp_message moves to DLQ after max retries."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    whatsapp_mock = AsyncMock()
    session_mock = AsyncMock()
    
    logger_mock = Mock()
    ctx = {
        "redis": redis_mock,
        "logger": logger_mock,
        "whatsapp_service": whatsapp_mock,
        "session": session_mock,
        "job_try": 3,  # Final attempt
    }
    
    with patch("app.workers.task_functions.get_inventory_search_service") as mock_service:
        service_instance = AsyncMock()
        service_instance.process_message.side_effect = Exception("API error")
        mock_service.return_value = service_instance
        
        result = await handle_incoming_whatsapp_message(
            ctx,
            "customer-123",
            "+1234567890",
            "Hello",
            "msg-123",
        )
        
        # Should return error status, not raise
        assert result["status"] == "dead_letter"
        assert "error" in result
        
        # Should have moved to DLQ
        assert redis_mock.hset.called
        assert redis_mock.lpush.called
