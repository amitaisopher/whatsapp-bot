from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class Customer(BaseModel):
    """Customer (dealership) model"""

    id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=255)
    contact_email: str | None = Field(None, max_length=255)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool = True
    api_key: str | None = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)
