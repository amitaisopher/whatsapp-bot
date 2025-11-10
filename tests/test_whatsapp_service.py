import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Generator

from app.services.whatsapp import (
    WhatsAppMessageProcessor,
    WhatsAppService,
    WhatsAppMessageType,
    create_default_message_processor,
)
from app.models.whatsapp import CustomerBoundMessage


class TestWhatsAppMessageProcessor:
    """Test the WhatsAppMessageProcessor class."""

    def test_init_sets_supported_message_types(self) -> None:
        """Test that the constructor correctly sets supported message types."""
        supported_types = {WhatsAppMessageType.TEXT, WhatsAppMessageType.IMAGE}
        processor = WhatsAppMessageProcessor(supported_message_types=supported_types)

        assert processor.supported_message_types == supported_types

    def test_should_process_message_with_supported_type(self) -> None:
        """Test that supported message types are marked for processing."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        assert processor.should_process_message("text") is True

    def test_should_process_message_with_unsupported_type(self) -> None:
        """Test that unsupported message types are not marked for processing."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        assert processor.should_process_message("image") is False
        assert processor.should_process_message("video") is False

    def test_extract_message_from_webhook_valid_text_message(self) -> None:
        """Test extracting a valid text message from webhook body."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        webhook_body = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "id": "msg123",
                                        "from": "+1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello World"},
                                    }
                                ],
                                "metadata": {"phone_number_id": "phone123"},
                            }
                        }
                    ]
                }
            ]
        }

        result = processor.extract_message_from_webhook(webhook_body)

        assert result is not None
        assert result["msg_type"] == "text"
        assert result["message"]["id"] == "msg123"
        assert result["message"]["from"] == "+1234567890"

    def test_extract_message_from_webhook_unsupported_type(self) -> None:
        """Test that unsupported message types return None."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        webhook_body = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "id": "msg123",
                                        "from": "+1234567890",
                                        "type": "image",
                                        "image": {"id": "img123"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        result = processor.extract_message_from_webhook(webhook_body)

        assert result is None

    def test_extract_message_from_webhook_no_messages(self) -> None:
        """Test handling webhook body with no messages."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        webhook_body = {"entry": [{"changes": [{"value": {"messages": []}}]}]}

        result = processor.extract_message_from_webhook(webhook_body)

        assert result is None

    def test_extract_message_from_webhook_malformed_body(self) -> None:
        """Test handling malformed webhook body."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        malformed_body = {"invalid": "structure"}

        result = processor.extract_message_from_webhook(malformed_body)

        assert result is None

    def test_create_customer_bound_message_text_type(self) -> None:
        """Test creating CustomerBoundMessage for text message."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={WhatsAppMessageType.TEXT}
        )

        msg = {
            "id": "msg123",
            "from": "+1234567890",
            "type": "text",
            "timestamp": "1234567890",
            "text": {"body": "Hello World"},
        }

        value = {"metadata": {"phone_number_id": "phone123"}}

        result = processor.create_customer_bound_message(
            msg=msg, value=value, msg_type="text", customer_id="customer123"
        )

        assert isinstance(result, CustomerBoundMessage)
        assert result.id == "msg123"
        assert result.from_ == "+1234567890"
        assert result.to == "phone123"
        assert result.text == "Hello World"
        assert result.type == "text"
        assert result.customer_id == "customer123"


class TestWhatsAppService:
    """Test the WhatsAppService class."""

    @pytest.fixture
    def mock_message_processor(self) -> Mock:
        """Create a mock message processor."""
        return Mock(spec=WhatsAppMessageProcessor)

    @pytest.fixture
    def mock_settings(self) -> Generator[MagicMock, None, None]:
        """Mock the settings."""
        with patch("app.services.whatsapp.settings") as mock_settings:
            mock_settings.whatsapp_access_token = "test_token"
            mock_settings.whatsapp_phone_number_id = "test_phone_id"
            mock_settings.debug = False
            yield mock_settings

    @pytest.fixture
    def whatsapp_service(
        self, mock_message_processor: Mock, mock_settings: MagicMock
    ) -> WhatsAppService:
        """Create a WhatsApp service instance for testing."""
        with (
            patch("app.services.whatsapp.WhatsApp"),
            patch("app.services.whatsapp.get_application_logger"),
        ):
            return WhatsAppService(message_processor=mock_message_processor)

    def test_init_requires_access_token(self, mock_message_processor: Mock) -> None:
        """Test that initialization fails without access token."""
        with patch("app.services.whatsapp.settings") as mock_settings:
            mock_settings.whatsapp_access_token = ""
            mock_settings.whatsapp_phone_number_id = "test_phone_id"

            with pytest.raises(ValueError, match="WhatsApp access token is required"):
                WhatsAppService(message_processor=mock_message_processor)

    def test_init_requires_phone_number_id(self, mock_message_processor: Mock) -> None:
        """Test that initialization fails without phone number ID."""
        with patch("app.services.whatsapp.settings") as mock_settings:
            mock_settings.whatsapp_access_token = "test_token"
            mock_settings.whatsapp_phone_number_id = ""

            with pytest.raises(
                ValueError, match="WhatsApp phone number ID is required"
            ):
                WhatsAppService(message_processor=mock_message_processor)

    @pytest.mark.asyncio
    async def test_handle_incoming_message_filters_unsupported_messages(
        self, whatsapp_service: WhatsAppService, mock_message_processor: Mock
    ) -> None:
        """Test that unsupported messages are filtered out."""
        mock_message_processor.extract_message_from_webhook.return_value = None

        await whatsapp_service.handle_incoming_message_and_push_to_queue(
            customer_id="test_customer",
            body={"entry": [{"changes": [{"value": {"messages": []}}]}]},
        )

        mock_message_processor.extract_message_from_webhook.assert_called_once()
        mock_message_processor.create_customer_bound_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_incoming_message_processes_supported_messages(
        self, whatsapp_service: WhatsAppService, mock_message_processor: Mock
    ) -> None:
        """Test that supported messages are processed and queued."""
        # Setup mock data
        message_data = {
            "message": {"id": "msg123", "from": "+1234567890"},
            "value": {"metadata": {"phone_number_id": "phone123"}},
            "msg_type": "text",
        }

        mock_customer_message = Mock(spec=CustomerBoundMessage)
        mock_customer_message.from_ = "+1234567890"
        mock_customer_message.text = "Hello"

        mock_message_processor.extract_message_from_webhook.return_value = message_data
        mock_message_processor.create_customer_bound_message.return_value = (
            mock_customer_message
        )

        # Mock queue service
        mock_queue_service = AsyncMock()
        mock_job = Mock()
        mock_job.job_id = "job123"
        mock_queue_service.enqueue.return_value = mock_job

        await whatsapp_service.handle_incoming_message_and_push_to_queue(
            customer_id="test_customer",
            body={"test": "body"},
            queue_service=mock_queue_service,
        )

        # Verify calls
        mock_message_processor.extract_message_from_webhook.assert_called_once()
        mock_message_processor.create_customer_bound_message.assert_called_once_with(
            msg=message_data["message"],
            value=message_data["value"],
            msg_type=message_data["msg_type"],
            customer_id="test_customer",
        )

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, whatsapp_service: WhatsAppService
    ) -> None:
        """Test successful message sending."""
        # Mock the AsyncMessage and its methods
        with patch("app.services.whatsapp.AsyncMessage") as mock_message_class:
            mock_message = Mock()
            mock_message_class.return_value = mock_message

            # Create a proper mock for the double await pattern
            async def mock_send_method(*args, **kwargs):
                # This is the first await - returns a coroutine/future
                async def mock_future():
                    # This is the second await - returns the actual response
                    return {"messages": [{"id": "msg_id_123"}]}

                return mock_future()

            mock_message.send = mock_send_method

            result = await whatsapp_service.send_message("+1234567890", "Hello World")

            assert result["success"] is True
            assert result["message_id"] == "msg_id_123"

    @pytest.mark.asyncio
    async def test_send_message_api_error(
        self, whatsapp_service: WhatsAppService
    ) -> None:
        """Test handling API errors when sending messages."""
        # Mock the AsyncMessage and its methods
        with patch("app.services.whatsapp.AsyncMessage") as mock_message_class:
            mock_message = Mock()
            mock_message_class.return_value = mock_message

            # Create a proper mock for the double await pattern with error
            async def mock_send_method(*args, **kwargs):
                # This is the first await - returns a coroutine/future
                async def mock_future():
                    # This is the second await - returns the error response
                    return {
                        "error": {
                            "code": 100,
                            "type": "OAuthException",
                            "message": "Invalid access token",
                        }
                    }

                return mock_future()

            mock_message.send = mock_send_method

            result = await whatsapp_service.send_message("+1234567890", "Hello World")

            assert result["success"] is False
            assert result["error"]["code"] == 100
            assert result["error"]["type"] == "OAuthException"


def test_create_default_message_processor() -> None:
    """Test the default message processor factory."""
    processor = create_default_message_processor()

    assert isinstance(processor, WhatsAppMessageProcessor)
    assert processor.supported_message_types == {WhatsAppMessageType.TEXT}


def test_get_whatsapp_service() -> None:
    """Test the WhatsApp service factory."""
    with (
        patch("app.services.whatsapp.settings") as mock_settings,
        patch("app.services.whatsapp.WhatsApp"),
        patch("app.services.whatsapp.get_application_logger"),
    ):
        mock_settings.whatsapp_access_token = "test_token"
        mock_settings.whatsapp_phone_number_id = "test_phone_id"
        mock_settings.debug = False

        from app.services.whatsapp import get_whatsapp_service

        service = get_whatsapp_service()

        assert isinstance(service, WhatsAppService)
        assert isinstance(service.message_processor, WhatsAppMessageProcessor)
        assert service.message_processor.supported_message_types == {"text"}


class TestMessageProcessorIntegration:
    """Integration tests for different message processor configurations."""

    def test_text_and_image_processor(self) -> None:
        """Test processor configured for text and image messages."""
        processor = WhatsAppMessageProcessor(
            supported_message_types={
                WhatsAppMessageType.TEXT,
                WhatsAppMessageType.IMAGE,
            }
        )

        assert processor.should_process_message("text") is True
        assert processor.should_process_message("image") is True
        assert processor.should_process_message("video") is False

    def test_service_with_custom_processor(self) -> None:
        """Test service with custom message processor."""
        custom_processor = WhatsAppMessageProcessor(
            supported_message_types={
                WhatsAppMessageType.TEXT,
                WhatsAppMessageType.IMAGE,
                WhatsAppMessageType.VIDEO,
            }
        )

        with (
            patch("app.services.whatsapp.settings") as mock_settings,
            patch("app.services.whatsapp.WhatsApp"),
            patch("app.services.whatsapp.get_application_logger"),
        ):
            mock_settings.whatsapp_access_token = "test_token"
            mock_settings.whatsapp_phone_number_id = "test_phone_id"
            mock_settings.debug = False

            service = WhatsAppService(message_processor=custom_processor)

            assert service.message_processor.supported_message_types == {
                WhatsAppMessageType.TEXT,
                WhatsAppMessageType.IMAGE,
                WhatsAppMessageType.VIDEO,
            }
