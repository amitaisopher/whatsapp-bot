from fastapi import APIRouter, Depends, Request, Path
from fastapi.responses import PlainTextResponse, JSONResponse
from app.core.auth import (
    verify_whatsapp_token,
    verify_whatsapp_payload_signature,
    verify_customer_api_key,
)
from typing import Annotated
from app.services.whatsapp import get_whatsapp_sevice, WhatsAppService

router = APIRouter()


@router.get(
    "/hook/{customer_api_key}", tags=["WhatsApp"], dependencies=[Depends(verify_customer_api_key)]
)
async def register_whatsapp_webhook(
    customer_api_key: Annotated[str, Path(title="Customer API Key")],
    challenge: Annotated[str, Depends(verify_whatsapp_token)],
):
    """Register WhatsApp webhook."""
    return PlainTextResponse(content=challenge)


@router.post(
    "/hook/{customer_api_key}",
    tags=["WhatsApp"],
    dependencies=[Depends(verify_whatsapp_payload_signature),
                  Depends(verify_customer_api_key)],
)
async def receive_whatsapp_message(
        req: Request,
        customer_api_key: Annotated[str, Path(title="Customer API Key")],
        whatsapp_service: WhatsAppService = Depends(get_whatsapp_sevice)):
    """Receive WhatsApp message, enqueue the message for processing, and return a 200 OK response."""
    body = await req.json()
    await whatsapp_service.handle_incoming_message_and_push_to_queue(body)
    return JSONResponse(status_code=200, content={"status": "received"})
