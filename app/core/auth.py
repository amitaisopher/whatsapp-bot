import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, status, Depends
from app.core.config import settings
from app.models.customer import Customer
from app.services.database import get_database_service, DatabaseService


def verify_whatsapp_token(request: Request):
    """
    Verify the incoming request token for WhatsApp Webhook
    """
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    verify_token = request.query_params.get("hub.verify_token")
    if mode and verify_token:
        if (
            mode == "subscribe"
            and verify_token == settings.whatsapp_webhook_verification_token
        ):
            logging.info("Webhook verification successful")
            # Respond with the challenge token
            return challenge
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        raise HTTPException(status_code=400, detail="Missing parameters")


def validate_signature(payload: str, signature: str):
    """
    Validate the signature of the incoming payload
    """
    # Use the App Secret to hash the payload
    secret = settings.whatsapp_app_secret.encode("utf-8")
    expected_hash_signature = hmac.new(
        secret, payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_hash_signature, signature)


async def verify_whatsapp_payload_signature(request: Request):
    """
    Verify the payload signature for WhatsApp Webhook
    """
    signature = request.headers.get(
        "X-Hub-Signature-256", "")[7:]  # Remove "sha256="
    body = await request.body()
    if not validate_signature(body.decode("utf-8"), signature):
        logging.info("Signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")
    return True


async def verify_customer_exist_and_active(customer_id: str, db_service: DatabaseService = Depends(get_database_service)):
    """
    Verify the customer ID from the request path exist in DB
    """
    # TODO: Implement actual DB check

    customer: Customer | None = await db_service.find_customer_by_id(customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized action")
    
    return True

async def get_active_api_key_of_customer(customer_id: str, db_service: DatabaseService = Depends(get_database_service)) -> str | None:
    customer: Customer | None = await db_service.find_customer_by_id(customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized action")
    return customer.api_key