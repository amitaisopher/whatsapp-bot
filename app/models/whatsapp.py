from pydantic import BaseModel, Field

class WhatsappIncomingMessage(BaseModel):
    """Model for incoming WhatsApp messages."""
    id: str
    from_: str
    to: str
    timestamp: str
    text: str | None = None
    type: str