from typing import Dict, Any
import asyncio
from arq.jobs import Job
from whatsapp import WhatsApp, AsyncMessage
from app.core.config import settings
from app.core.logging import get_application_logger
from app.models.whatsapp import CustomerBoundMessage
from app.services.queue import ArqService, get_arq_service
from functools import lru_cache


class WhatsAppService:
    def __init__(self) -> None:
        if not settings.whatsapp_access_token:
            raise ValueError("WhatsApp access token is required")
        if not settings.whatsapp_phone_number_id:
            raise ValueError("WhatsApp phone number ID is required")

        self.whatsapp_client: WhatsApp = WhatsApp(
            token=settings.whatsapp_access_token,
            phone_number_id={
                "my_whatsapp_phone_number_id": settings.whatsapp_phone_number_id},
            debug=settings.debug,
            logger=False
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
        message = AsyncMessage(
            instance=self.whatsapp_client, content=content, to=to)

        try:
            # Get the asyncio Future from send()
            send_future = await message.send(sender='my_whatsapp_phone_number_id')

            # Wait for the actual HTTP response
            response = await send_future

            # Check if the response indicates success
            if self._is_successful_response(response):
                self.logger.info(f"Successfully sent WhatsApp message to {to}")
                return {
                    "success": True,
                    "message_id": response.get("messages", [{}])[0].get("id"),
                    "response": response
                }
            else:
                # Handle API errors
                error_info = self._extract_error_info(response)
                self.logger.error(
                    f"WhatsApp API error when sending to {to}: {error_info}")
                return {
                    "success": False,
                    "error": error_info,
                    "response": response
                }

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout while sending WhatsApp message to {to}")
            return {
                "success": False,
                "error": "Request timeout",
                "response": None
            }
        except Exception as e:
            self.logger.exception(
                f"Exception occurred while sending WhatsApp message to {to}: {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "response": None
            }

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
                "fbtrace_id": error.get("fbtrace_id")
            }

        # If no explicit error but also no success indicators
        return {
            "code": "UNKNOWN",
            "type": "UNKNOWN_ERROR",
            "message": "Unexpected response format",
            "response": response
        }

    async def handle_incoming_message_and_push_to_queue(self, customer_id: str,  body: dict, queue_service: ArqService = get_arq_service()) -> None:
        # Example structure: entry → changes → value → messages
        try:
            entry = body["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages")
            if not messages:
                # no new message event for us
                return
            msg = messages[0]
        except Exception:
            # self.logger.error("Failed to parse webhook body: %s", e)
            return

         # Extract fields
        sender = msg.get("from")              # phone number of sender
        message_id = msg.get("id")            # message id
        msg_type = msg.get("type")            # e.g., "text", "image", etc
        text_body = None
        if msg_type == "text":
            text_body = msg.get("text", {}).get("body")
        else:
            # you can extend: if media, interactive, etc
            text_body = f"<{msg_type} message>"

        # self.logger.info("Incoming message from %s: type=%s, content=%s", sender, msg_type, text_body)

        whatsapp_incoming_message = CustomerBoundMessage(
            id=message_id,
            from_=sender,
            to=value.get("metadata", {}).get("phone_number_id", ""),
            timestamp=msg.get("timestamp", ""),
            text=text_body,
            type=msg_type,
            customer_id=customer_id
        )
        try:
            async with queue_service:
                job_id: Job | None = await queue_service.enqueue('send_whatsapp_message', to=whatsapp_incoming_message.from_, content=whatsapp_incoming_message.text)
                # if job_id:
                #     self.logger.info(f'Enqueued WhatsApp message processing job: {job_id.job_id}')
                # else:
                #     self.logger.error('Failed to enqueue WhatsApp message processing job')
        except Exception:
            # self.logger.error("Failed to enqueue job: %s", e)
            return


@lru_cache()
def get_whatsapp_sevice() -> WhatsAppService:
    return WhatsAppService()
