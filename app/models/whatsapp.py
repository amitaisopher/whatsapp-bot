from pydantic import BaseModel

class WhatsappIncomingMessage(BaseModel):
    """Model for incoming WhatsApp messages."""
    id: str
    from_: str
    to: str
    timestamp: str
    text: str | None = None
    type: str

class CustomerBoundMessage(WhatsappIncomingMessage):
    """Model for messages bound to a specific customer."""
    customer_id: str