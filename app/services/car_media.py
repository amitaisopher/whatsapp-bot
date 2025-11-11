"""Service for managing car media (images, videos, documents)."""

from typing import Optional
from uuid import UUID

from supabase import Client

from app.models.car_media import (
    CarMedia,
    CarMediaCreate,
    CarMediaListResponse,
    CarMediaUpdate,
    MediaType,
)


class CarMediaService:
    """Service for managing car media."""

    def __init__(self, supabase_client: Client):
        """Initialize the car media service.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client

    async def create_media(self, media: CarMediaCreate) -> CarMedia:
        """Create a new car media entry.

        Args:
            media: Car media data to create

        Returns:
            Created car media

        Raises:
            Exception: If creation fails
        """
        response = (
            self.supabase.table("car_media")
            .insert(media.model_dump(mode='json'))
            .execute()
        )

        if not response.data:
            raise Exception("Failed to create car media")

        return CarMedia(**response.data[0])

    async def get_media_by_id(
        self, media_id: UUID, customer_id: UUID
    ) -> Optional[CarMedia]:
        """Get a car media entry by ID.

        Args:
            media_id: Media ID
            customer_id: Customer ID for RLS

        Returns:
            Car media if found, None otherwise
        """
        response = (
            self.supabase.table("car_media")
            .select("*")
            .eq("id", str(media_id))
            .eq("customer_id", str(customer_id))
            .execute()
        )

        if not response.data:
            return None

        return CarMedia(**response.data[0])

    async def get_car_media(
        self, car_id: int, customer_id: UUID, include_inactive: bool = False
    ) -> CarMediaListResponse:
        """Get all media for a car organized by type.

        Args:
            car_id: Car ID
            customer_id: Customer ID for RLS
            include_inactive: Whether to include inactive media

        Returns:
            Car media organized by type
        """
        query = (
            self.supabase.table("car_media")
            .select("*")
            .eq("car_id", car_id)
            .eq("customer_id", str(customer_id))
            .order("display_order", desc=False)
            .order("created_at", desc=False)
        )

        if not include_inactive:
            query = query.eq("is_active", True)

        response = query.execute()

        media_list = [CarMedia(**item) for item in response.data]

        # Organize by type
        images = [m for m in media_list if m.media_type == MediaType.IMAGE]
        videos = [m for m in media_list if m.media_type == MediaType.VIDEO]
        documents = [
            m
            for m in media_list
            if m.media_type in [MediaType.DOCUMENT, MediaType.THREE_SIXTY_VIEW]
        ]
        primary_image = next(
            (m for m in images if m.is_primary), images[0] if images else None
        )

        return CarMediaListResponse(
            car_id=car_id,
            total_count=len(media_list),
            images=images,
            videos=videos,
            documents=documents,
            primary_image=primary_image,
        )

    async def update_media(
        self, media_id: UUID, customer_id: UUID, update_data: CarMediaUpdate
    ) -> Optional[CarMedia]:
        """Update a car media entry.

        Args:
            media_id: Media ID
            customer_id: Customer ID for RLS
            update_data: Fields to update

        Returns:
            Updated car media if found, None otherwise
        """
        # Only include fields that were actually set
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            # Nothing to update, fetch and return existing
            return await self.get_media_by_id(media_id, customer_id)

        response = (
            self.supabase.table("car_media")
            .update(update_dict)
            .eq("id", str(media_id))
            .eq("customer_id", str(customer_id))
            .execute()
        )

        if not response.data:
            return None

        return CarMedia(**response.data[0])

    async def set_primary_image(
        self, media_id: UUID, car_id: int, customer_id: UUID
    ) -> bool:
        """Set a media item as the primary image for a car.

        This will unset any existing primary image for the car.

        Args:
            media_id: Media ID to set as primary
            car_id: Car ID
            customer_id: Customer ID for RLS

        Returns:
            True if successful, False otherwise
        """
        # First, unset all primary flags for this car
        self.supabase.table("car_media").update({"is_primary": False}).eq(
            "car_id", car_id
        ).eq("customer_id", str(customer_id)).execute()

        # Then set the specified media as primary
        response = (
            self.supabase.table("car_media")
            .update({"is_primary": True})
            .eq("id", str(media_id))
            .eq("customer_id", str(customer_id))
            .execute()
        )

        return bool(response.data)

    async def reorder_media(
        self,
        car_id: int,
        customer_id: UUID,
        media_order: list[dict[str, int]],
    ) -> bool:
        """Reorder media for a car.

        Args:
            car_id: Car ID
            customer_id: Customer ID for RLS
            media_order: List of dicts with 'id' and 'display_order' keys
                Example: [{'id': 'uuid1', 'display_order': 0}, {'id': 'uuid2', 'display_order': 1}]

        Returns:
            True if successful, False otherwise
        """
        try:
            for item in media_order:
                media_id = item["id"]
                display_order = item["display_order"]

                self.supabase.table("car_media").update(
                    {"display_order": display_order}
                ).eq("id", str(media_id)).eq("car_id", car_id).eq(
                    "customer_id", str(customer_id)
                ).execute()

            return True
        except Exception:
            return False

    async def delete_media(self, media_id: UUID, customer_id: UUID) -> bool:
        """Soft delete a car media entry by setting is_active to False.

        Args:
            media_id: Media ID
            customer_id: Customer ID for RLS

        Returns:
            True if successful, False otherwise
        """
        response = (
            self.supabase.table("car_media")
            .update({"is_active": False})
            .eq("id", str(media_id))
            .eq("customer_id", str(customer_id))
            .execute()
        )

        return bool(response.data)

    async def hard_delete_media(self, media_id: UUID, customer_id: UUID) -> bool:
        """Permanently delete a car media entry.

        Args:
            media_id: Media ID
            customer_id: Customer ID for RLS

        Returns:
            True if successful, False otherwise
        """
        response = (
            self.supabase.table("car_media")
            .delete()
            .eq("id", str(media_id))
            .eq("customer_id", str(customer_id))
            .execute()
        )

        return bool(response.data)

    async def bulk_create_media(
        self, media_list: list[CarMediaCreate]
    ) -> list[CarMedia]:
        """Create multiple car media entries at once.

        Args:
            media_list: List of car media data to create

        Returns:
            List of created car media

        Raises:
            Exception: If creation fails
        """
        data = [media.model_dump(mode='json') for media in media_list]
        response = self.supabase.table("car_media").insert(data).execute()

        if not response.data:
            raise Exception("Failed to create car media")

        return [CarMedia(**item) for item in response.data]
