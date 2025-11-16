"""Tests for task deduplication functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from arq import Retry
from app.workers.task_functions import (
    handle_incoming_whatsapp_message,
    send_whatsapp_message,
    download_content,
)
from app.workers.job_deduplication import (
    is_job_already_processed,
    mark_job_as_processed,
)


class TestTaskDeduplication:
    """Test job deduplication functionality."""

    @pytest.fixture
    def mock_ctx(self) -> dict:
        """Create a mock context for testing."""
        redis_mock = AsyncMock()
        return {
            "logger": Mock(),
            "session": AsyncMock(),
            "whatsapp_service": AsyncMock(),
            "redis": redis_mock,
        }

    @pytest.mark.asyncio
    async def test_job_deduplication_new_job(self, mock_ctx: dict) -> None:
        """Test that new jobs are not marked as processed."""
        mock_ctx["redis"].get.return_value = None

        result = await is_job_already_processed(mock_ctx, "test_job")

        assert result is False
        mock_ctx["redis"].get.assert_called_once_with("job_processed:test_job")

    @pytest.mark.asyncio
    async def test_job_deduplication_existing_job(self, mock_ctx: dict) -> None:
        """Test that existing jobs are marked as processed."""
        mock_ctx["redis"].get.return_value = "1"

        result = await is_job_already_processed(mock_ctx, "test_job")

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_job_as_processed(self, mock_ctx: dict) -> None:
        """Test marking a job as processed."""
        await mark_job_as_processed(mock_ctx, "test_job", 300)

        mock_ctx["redis"].setex.assert_called_once_with(
            "job_processed:test_job", 300, "1"
        )

    @pytest.mark.asyncio
    async def test_download_content_deduplication(self, mock_ctx: dict) -> None:
        """Test that duplicate download jobs are skipped."""
        # Setup: Job already processed
        mock_ctx["redis"].get.return_value = "1"

        result = await download_content(mock_ctx, "http://example.com")

        assert "Already downloaded content" in result
        mock_ctx["logger"].info.assert_called_with(
            f"Job download:{hash('http://example.com')} already processed, skipping"
        )

    @pytest.mark.asyncio
    async def test_download_content_successful_processing(self, mock_ctx: dict) -> None:
        """Test successful download content processing."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        result = await download_content(mock_ctx, "http://example.com")

        assert "Downloaded content from http://example.com" in result
        # Check that job was marked as processed
        mock_ctx["redis"].setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_message_deduplication(self, mock_ctx: dict) -> None:
        """Test that duplicate WhatsApp messages are skipped."""
        # Setup: Job already processed
        mock_ctx["redis"].get.return_value = "1"

        result = await handle_incoming_whatsapp_message(
            mock_ctx, "customer123", "+1234567890", "Hello", "msg123"
        )

        assert result["status"] == "already_processed"
        assert result["job_key"] == "msg123"

    @pytest.mark.asyncio
    async def test_whatsapp_message_successful_processing(self, mock_ctx: dict) -> None:
        """Test successful WhatsApp message processing."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        # Mock inventory search service
        with patch(
            "app.workers.task_functions.get_inventory_search_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.process_message.return_value = {"reply": "Test response"}
            mock_get_service.return_value = mock_service

            # Mock WhatsApp service response
            mock_ctx["whatsapp_service"].send_message.return_value = {"success": True}

            result = await handle_incoming_whatsapp_message(
                mock_ctx, "customer123", "+1234567890", "Hello", "msg123"
            )

            assert result["status"] == "success"
            assert result["job_key"] == "msg123"
            assert result["message_sent"] == "Test response"
            mock_ctx["redis"].setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_message_no_response(self, mock_ctx: dict) -> None:
        """Test WhatsApp message processing when no response is received."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        # Mock inventory search service to return None
        with patch(
            "app.workers.task_functions.get_inventory_search_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.process_message.return_value = None
            mock_get_service.return_value = mock_service

            result = await handle_incoming_whatsapp_message(
                mock_ctx, "customer123", "+1234567890", "Hello", "msg123"
            )

            assert result["status"] == "no_response"
            assert result["job_key"] == "msg123"
            # Should still mark as processed to avoid infinite retries
            mock_ctx["redis"].setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_message_send_failure(self, mock_ctx: dict) -> None:
        """Test WhatsApp message processing when send fails."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        # Mock inventory search service
        with patch(
            "app.workers.task_functions.get_inventory_search_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.process_message.return_value = {"reply": "Test response"}
            mock_get_service.return_value = mock_service

            # Mock WhatsApp service response to fail
            mock_ctx["whatsapp_service"].send_message.return_value = None

            # Should raise Retry exception on first attempt
            with pytest.raises(Retry):
                await handle_incoming_whatsapp_message(
                    mock_ctx, "customer123", "+1234567890", "Hello", "msg123"
                )

            # Should NOT mark as processed on failure
            mock_ctx["redis"].setex.assert_not_called()
            mock_ctx["redis"].setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_deduplication(self, mock_ctx: dict) -> None:
        """Test that duplicate send message jobs are skipped."""
        # Setup: Job already processed
        mock_ctx["redis"].get.return_value = "1"

        result = await send_whatsapp_message(
            mock_ctx, "+1234567890", "Hello", "send123"
        )

        assert "Already sent" in result

    @pytest.mark.asyncio
    async def test_send_message_successful_processing(self, mock_ctx: dict) -> None:
        """Test successful send message processing."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        # Mock successful send
        mock_ctx["whatsapp_service"].send_message.return_value = {"success": True}

        result = await send_whatsapp_message(
            mock_ctx, "+1234567890", "Hello", "send123"
        )

        assert "Sent WhatsApp message to +1234567890" in result
        mock_ctx["redis"].setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self, mock_ctx: dict) -> None:
        """Test send message processing when send fails."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        # Mock failed send
        mock_ctx["whatsapp_service"].send_message.return_value = None

        # Should raise Retry exception on first attempt
        with pytest.raises(Retry):
            await send_whatsapp_message(mock_ctx, "+1234567890", "Hello", "send123")

        # Should NOT mark as processed on failure
        mock_ctx["redis"].setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_job_key_generation_consistency(self, mock_ctx: dict) -> None:
        """Test that job keys are generated consistently for the same parameters."""
        # Setup: New job
        mock_ctx["redis"].get.return_value = None

        # Mock services
        with patch(
            "app.workers.task_functions.get_inventory_search_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.process_message.return_value = {"response": "Test"}
            mock_get_service.return_value = mock_service
            mock_ctx["whatsapp_service"].send_message.return_value = {"success": True}

            # Process same message twice (without message_id)
            result1 = await handle_incoming_whatsapp_message(
                mock_ctx, "customer123", "+1234567890", "Hello"
            )

            # Reset redis mock for second call
            mock_ctx["redis"].get.return_value = "1"  # Should be marked as processed

            result2 = await handle_incoming_whatsapp_message(
                mock_ctx, "customer123", "+1234567890", "Hello"
            )

            # First should succeed, second should be skipped
            assert result1["status"] == "success"
            assert result2["status"] == "already_processed"
            # Both should have the same job_key
            assert result1["job_key"] == result2["job_key"]

    @pytest.mark.asyncio
    async def test_no_redis_context(self) -> None:
        """Test behavior when Redis is not available in context."""
        ctx_without_redis = {"logger": Mock()}

        # Should return False when no redis in context
        result = await is_job_already_processed(ctx_without_redis, "test_job")
        assert result is False

        # Should not raise error when marking job as processed
        await mark_job_as_processed(ctx_without_redis, "test_job")
