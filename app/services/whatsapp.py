from typing import Dict, Any, Optional, Set
import asyncio
from enum import StrEnum
from arq.jobs import Job
from whatsapp import WhatsApp, AsyncMessage
from app.core.config import settings
from app.core.logging import get_application_logger
from app.models.whatsapp import CustomerBoundMessage
from app.services.queue import ArqService, get_arq_service
from functools import lru_cache

logger = get_application_logger()


class WhatsAppMessageType(StrEnum):
    """Enum for WhatsApp message types."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    ORDER = "order"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class WhatsAppMessageProcessor:
    """Handles processing and filtering of incoming WhatsApp messages."""

    def __init__(self, supported_message_types: Set[WhatsAppMessageType]) -> None:
        """
        Initialize the message processor with supported message types.

        Args:
            supported_message_types: Set of message types to process (e.g., {WhatsAppMessageType.TEXT, WhatsAppMessageType.IMAGE})
        """
        self.supported_message_types = supported_message_types
        self.logger = get_application_logger()

    def should_process_message(self, msg_type: str) -> bool:
        """
        Determine if a message type should be processed.

        Args:
            msg_type: The type of the WhatsApp message

        Returns:
            True if the message should be processed, False otherwise
        """
        return msg_type in self.supported_message_types

    def extract_message_from_webhook(
        self, body: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract message data from WhatsApp webhook body.

        Args:
            body: The webhook request body

        Returns:
            Dict containing message data or None if no valid message found
        """
        try:
            entry = body["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages")

            if not messages:
                self.logger.debug("No messages found in webhook body")
                return None

            msg = messages[0]
            msg_type = msg.get("type")

            if not self.should_process_message(msg_type):
                self.logger.info(
                    f"Ignoring message of type '{msg_type}' - not supported"
                )
                return None

            return {"message": msg, "value": value, "msg_type": msg_type}

        except (KeyError, IndexError, TypeError) as e:
            self.logger.error(f"Failed to parse webhook body: {e}")
            return None

    def create_customer_bound_message(
        self,
        msg: Dict[str, Any],
        value: Dict[str, Any],
        msg_type: str,
        customer_id: str,
    ) -> CustomerBoundMessage:
        """
        Create a CustomerBoundMessage from parsed message data.

        Args:
            msg: The message object from webhook
            value: The value object from webhook
            msg_type: Type of the message
            customer_id: ID of the customer

        Returns:
            CustomerBoundMessage instance
        """
        sender = msg.get("from", "")
        message_id = msg.get("id", "")

        # Extract text content (only for text messages at this point)
        text_body = None
        if msg_type == "text":
            text_body = msg.get("text", {}).get("body")

        return CustomerBoundMessage(
            id=message_id,
            from_=sender,
            to=value.get("metadata", {}).get("phone_number_id", ""),
            timestamp=msg.get("timestamp", ""),
            text=text_body,
            type=msg_type,
            customer_id=customer_id,
        )


class WhatsAppService:
    def __init__(self, message_processor: WhatsAppMessageProcessor) -> None:
        """
        Initialize WhatsApp service with dependency injection.

        Args:
            message_processor: Instance of WhatsAppMessageProcessor for handling messages
        """
        if not settings.whatsapp_access_token:
            raise ValueError("WhatsApp access token is required")
        if not settings.whatsapp_phone_number_id:
            raise ValueError("WhatsApp phone number ID is required")

        self.message_processor = message_processor
        self.whatsapp_client: WhatsApp = WhatsApp(
            token=settings.whatsapp_access_token,
            phone_number_id={
                "my_whatsapp_phone_number_id": settings.whatsapp_phone_number_id
            },
            debug=settings.debug,
            logger=False,
        )
        self.logger = get_application_logger()

    async def send_message(self, to: str, content: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message and handle the API response.

        Args:
            to: Phone number to send message to
            content: Message content

        Returns:
            Dict containing success status and response data
        """
        message = AsyncMessage(instance=self.whatsapp_client, content=content, to=to)

        try:
            # Get the asyncio Future from send()
            send_future = await message.send(sender="my_whatsapp_phone_number_id")

            # Wait for the actual HTTP response
            response = await send_future

            # Check if the response indicates success
            if self._is_successful_response(response):
                self.logger.info(f"Successfully sent WhatsApp message to {to}")
                return {
                    "success": True,
                    "message_id": response.get("messages", [{}])[0].get("id"),
                    "response": response,
                }
            else:
                # Handle API errors
                error_info = self._extract_error_info(response)
                self.logger.error(
                    f"WhatsApp API error when sending to {to}: {error_info}"
                )
                return {"success": False, "error": error_info, "response": response}

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout while sending WhatsApp message to {to}")
            return {"success": False, "error": "Request timeout", "response": None}
        except Exception as e:
            self.logger.exception(
                f"Exception occurred while sending WhatsApp message to {to}: {e}"
            )
            return {"success": False, "error": f"Exception: {str(e)}", "response": None}

    def _is_successful_response(self, response: Dict[str, Any]) -> bool:
        """
        Check if the WhatsApp API response indicates success.

        Args:
            response: The API response dictionary

        Returns:
            True if successful, False otherwise
        """
        # Meta's WhatsApp API returns a 'messages' array on success
        # and an 'error' object on failure
        if "error" in response:
            return False

        if "messages" in response and response["messages"]:
            return True

        return False

    def _extract_error_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract error information from WhatsApp API response.

        Args:
            response: The API response dictionary

        Returns:
            Dictionary containing error details
        """
        if "error" in response:
            error = response["error"]
            return {
                "code": error.get("code"),
                "type": error.get("type"),
                "message": error.get("message"),
                "error_subcode": error.get("error_subcode"),
                "fbtrace_id": error.get("fbtrace_id"),
            }

        # If no explicit error but also no success indicators
        return {
            "code": "UNKNOWN",
            "type": "UNKNOWN_ERROR",
            "message": "Unexpected response format",
            "response": response,
        }

    async def handle_incoming_message_and_push_to_queue(
        self,
        customer_id: str,
        body: Dict[str, Any],
        queue_service: ArqService = get_arq_service(),
    ) -> None:
        """
        Handle incoming WhatsApp webhook message and push to processing queue.
        Only processes supported message types based on the injected message processor.

        Args:
            customer_id: ID of the customer
            body: The webhook request body
            queue_service: The queue service for processing messages
        """
        # Extract and validate message using the injected processor
        message_data = self.message_processor.extract_message_from_webhook(body)

        if not message_data:
            # Message was filtered out or parsing failed
            return

        # Create the customer bound message
        try:
            whatsapp_incoming_message = (
                self.message_processor.create_customer_bound_message(
                    msg=message_data["message"],
                    value=message_data["value"],
                    msg_type=message_data["msg_type"],
                    customer_id=customer_id,
                )
            )

            self.logger.info(
                f"Processing incoming {message_data['msg_type']} message from {whatsapp_incoming_message.from_}"
            )

        except Exception as e:
            self.logger.error(f"Failed to create customer bound message: {e}")
            return

        # Enqueue the message for processing
        try:
            async with queue_service:
                # job_id: Job | None = await queue_service.enqueue(
                #     "send_whatsapp_message",
                #     to=whatsapp_incoming_message.from_,
                #     content=whatsapp_incoming_message.text,
                # )
                job_id: Job | None = await queue_service.enqueue(
                    'handle_incoming_whatsapp_message',
                    customer_id=customer_id,
                    from_number=whatsapp_incoming_message.from_,
                    user_message=whatsapp_incoming_message.text,
                    message_id=whatsapp_incoming_message.id  # Pass message ID for deduplication
                )
                if job_id:
                    self.logger.info(
                        f"Enqueued WhatsApp message processing job: {job_id.job_id}"
                    )
                else:
                    self.logger.error(
                        "Failed to enqueue WhatsApp message processing job"
                    )
        except Exception as e:
            self.logger.error(f"Failed to enqueue job: {e}")
            return


def create_default_message_processor() -> WhatsAppMessageProcessor:
    """
    Create a default message processor that only handles text messages.

    Returns:
        WhatsAppMessageProcessor instance configured for text messages only
    """
    return WhatsAppMessageProcessor(supported_message_types={WhatsAppMessageType.TEXT})


@lru_cache()
def get_whatsapp_service() -> WhatsAppService:
    """
    Get a WhatsApp service instance with default message processor.

    Returns:
        WhatsAppService instance with text-only message processing
    """
    message_processor = create_default_message_processor()
    return WhatsAppService(message_processor=message_processor)
