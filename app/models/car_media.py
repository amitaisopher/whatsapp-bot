"""Models for car media (images, videos, documents)."""

from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class MediaType(StrEnum):
    """Enum for media types."""

    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    THREE_SIXTY_VIEW = "three_sixty_view"
    THUMBNAIL = "thumbnail"


class StorageProvider(StrEnum):
    """Enum for storage providers."""

    CLOUDINARY = "cloudinary"
    S3 = "s3"
    LOCAL = "local"
    SUPABASE = "supabase"


class CarMediaBase(BaseModel):
    """Base model for car media."""

    media_type: MediaType = Field(default=MediaType.IMAGE)
    url: str = Field(..., max_length=2048)
    storage_provider: StorageProvider = Field(default=StorageProvider.CLOUDINARY)
    file_name: Optional[str] = Field(None, max_length=255)
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    alt_text: Optional[str] = None
    display_order: int = Field(default=0, ge=0)
    is_primary: bool = Field(default=False)
    is_active: bool = Field(default=True)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://", "/")):
            raise ValueError("URL must start with http://, https://, or /")
        return v


class CarMediaCreate(CarMediaBase):
    """Model for creating car media."""

    car_id: int = Field(..., gt=0)
    customer_id: UUID


class CarMediaUpdate(BaseModel):
    """Model for updating car media."""

    url: Optional[str] = Field(None, max_length=2048)
    file_name: Optional[str] = Field(None, max_length=255)
    mime_type: Optional[str] = Field(None, max_length=100)
    alt_text: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None


class CarMedia(CarMediaBase):
    """Model for car media with all fields."""

    id: UUID
    car_id: int
    customer_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CarMediaListResponse(BaseModel):
    """Response model for listing car media organized by type."""

    car_id: int
    total_count: int
    images: list[CarMedia]
    videos: list[CarMedia]
    documents: list[CarMedia]
    primary_image: Optional[CarMedia] = None
