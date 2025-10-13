from arq.jobs import Job
from whatsapp import WhatsApp, AsyncMessage
from app.core.config import settings
from app.models.whatsapp import WhatsappIncomingMessage
from app.services.queue import ArqService, get_arq_service
from app.core.logging import get_application_logger
from functools import lru_cache

class WhatsAppService:
    def __init__(self) -> None:
        if not settings.whatsapp_access_token:
            raise ValueError("WhatsApp access token is required")
        if not settings.whatsapp_phone_number_id:
            raise ValueError("WhatsApp phone number ID is required")
        
        self.whatsapp_client: WhatsApp = WhatsApp(
            token=settings.whatsapp_access_token,
            phone_number_id={"my_whatsapp_phone_number_id": settings.whatsapp_phone_number_id},
            debug=settings.debug,
            logger=False
        )

    async def send_message(self, to: str, content: str) -> None:
        message = AsyncMessage(instance=self.whatsapp_client, content=content, to=to) # this is your message instance, sender is the phone number key you want to use
        try:
            await message.mark_as_read()
            await message.send(sender='my_whatsapp_phone_number_id')
            # logger.info(f"Sent WhatsApp message to {to}: {content}")
        except Exception as e:
            # logger.error(f"Failed to send WhatsApp message to {to}: {e}")
            import logging
            logging.exception(e)
            print(f"Failed to send WhatsApp message to {to}: {e}")

    async def handle_incoming_message_and_push_to_queue(self, body: dict, queue_service: ArqService = get_arq_service()) -> None:
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
        except Exception as e:
            # logger.error("Failed to parse webhook body: %s", e)
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

        # logger.info("Incoming message from %s: type=%s, content=%s", sender, msg_type, text_body)

        whatsapp_incoming_message = WhatsappIncomingMessage(
            id=message_id,
            from_=sender,
            to=value.get("metadata", {}).get("phone_number_id", ""),
            timestamp=msg.get("timestamp", ""),
            text=text_body,
            type=msg_type
        )
        try:
            async with queue_service:
                job_id: Job | None = await queue_service.enqueue('send_whatsapp_message', to=whatsapp_incoming_message.from_, content=whatsapp_incoming_message.text)
                # if job_id:
                #     logger.info(f'Enqueued WhatsApp message processing job: {job_id.job_id}')
                # else:
                #     logger.error('Failed to enqueue WhatsApp message processing job')
        except Exception as e:
            # logger.error("Failed to enqueue job: %s", e)
            return

@lru_cache()
def get_whatsapp_sevice() -> WhatsAppService:
    return WhatsAppService()
