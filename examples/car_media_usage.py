"""Examples of using the CarMediaService."""

import asyncio
from uuid import UUID

from supabase import create_client

from app.models.car_media import (
    CarMediaCreate,
    CarMediaUpdate,
    MediaType,
    StorageProvider,
)
from app.services.car_media import CarMediaService


async def main():
    """Run example usage."""
    # Initialize Supabase client (replace with actual credentials)
    supabase = create_client(
        supabase_url="YOUR_SUPABASE_URL",
        supabase_key="YOUR_SUPABASE_KEY",
    )

    # Initialize service
    media_service = CarMediaService(supabase)

    # Example customer and car IDs
    customer_id = UUID("12345678-1234-5678-1234-567812345678")
    car_id = 1

    # Example 1: Create a single image
    print("\n=== Creating a single image ===")
    new_image = CarMediaCreate(
        car_id=car_id,
        customer_id=customer_id,
        media_type=MediaType.IMAGE,
        url="https://res.cloudinary.com/example/image/upload/v1234/car_front.jpg",
        storage_provider=StorageProvider.CLOUDINARY,
        file_name="car_front.jpg",
        mime_type="image/jpeg",
        file_size_bytes=245678,
        width=1920,
        height=1080,
        alt_text="Front view of the car",
        display_order=0,
        is_primary=True,
    )

    created_image = await media_service.create_media(new_image)
    print(f"Created image: {created_image.id}")

    # Example 2: Bulk create multiple images
    print("\n=== Bulk creating multiple images ===")
    images_to_create = [
        CarMediaCreate(
            car_id=car_id,
            customer_id=customer_id,
            media_type=MediaType.IMAGE,
            url=f"https://res.cloudinary.com/example/image/upload/v1234/car_{view}.jpg",
            storage_provider=StorageProvider.CLOUDINARY,
            file_name=f"car_{view}.jpg",
            mime_type="image/jpeg",
            alt_text=f"{view.title()} view of the car",
            display_order=idx + 1,
        )
        for idx, view in enumerate(["side", "rear", "interior", "dashboard"])
    ]

    created_images = await media_service.bulk_create_media(images_to_create)
    print(f"Created {len(created_images)} images")

    # Example 3: Create a video
    print("\n=== Creating a video ===")
    new_video = CarMediaCreate(
        car_id=car_id,
        customer_id=customer_id,
        media_type=MediaType.VIDEO,
        url="https://res.cloudinary.com/example/video/upload/v1234/car_tour.mp4",
        storage_provider=StorageProvider.CLOUDINARY,
        file_name="car_tour.mp4",
        mime_type="video/mp4",
        file_size_bytes=5000000,
        alt_text="360 tour of the car",
        display_order=0,
    )

    created_video = await media_service.create_media(new_video)
    print(f"Created video: {created_video.id}")

    # Example 4: Get all media for a car
    print("\n=== Getting all media for a car ===")
    car_media = await media_service.get_car_media(car_id, customer_id)
    print(f"Total media count: {car_media.total_count}")
    print(f"Images: {len(car_media.images)}")
    print(f"Videos: {len(car_media.videos)}")
    print(f"Documents: {len(car_media.documents)}")
    if car_media.primary_image:
        print(f"Primary image: {car_media.primary_image.url}")

    # Example 5: Update media metadata
    print("\n=== Updating media metadata ===")
    if created_image:
        update_data = CarMediaUpdate(
            alt_text="Updated: Front view of the car in showroom",
            display_order=10,
        )
        updated_media = await media_service.update_media(
            created_image.id, customer_id, update_data
        )
        if updated_media:
            print(f"Updated media: {updated_media.alt_text}")

    # Example 6: Set a different image as primary
    print("\n=== Setting a different primary image ===")
    if len(created_images) > 0:
        success = await media_service.set_primary_image(
            created_images[0].id, car_id, customer_id
        )
        print(f"Set primary image: {success}")

        # Verify
        car_media = await media_service.get_car_media(car_id, customer_id)
        if car_media.primary_image:
            print(f"New primary image: {car_media.primary_image.file_name}")

    # Example 7: Reorder media
    print("\n=== Reordering media ===")
    media_order = [
        {"id": str(created_images[2].id), "display_order": 0},
        {"id": str(created_images[1].id), "display_order": 1},
        {"id": str(created_images[0].id), "display_order": 2},
    ]
    success = await media_service.reorder_media(car_id, customer_id, media_order)
    print(f"Reordered media: {success}")

    # Example 8: Soft delete media
    print("\n=== Soft deleting media ===")
    if created_image:
        success = await media_service.delete_media(created_image.id, customer_id)
        print(f"Soft deleted media: {success}")

        # Verify it's not returned by default
        car_media = await media_service.get_car_media(car_id, customer_id)
        print(f"Active media count: {car_media.total_count}")

        # But can still be retrieved with include_inactive
        car_media_all = await media_service.get_car_media(
            car_id, customer_id, include_inactive=True
        )
        print(f"Total media count (including inactive): {car_media_all.total_count}")

    # Example 9: Get specific media by ID
    print("\n=== Getting specific media by ID ===")
    if created_video:
        media = await media_service.get_media_by_id(created_video.id, customer_id)
        if media:
            print(f"Found media: {media.file_name} ({media.media_type})")

    # Example 10: Hard delete media (permanently)
    print("\n=== Hard deleting media ===")
    if created_video:
        success = await media_service.hard_delete_media(
            created_video.id, customer_id
        )
        print(f"Permanently deleted media: {success}")


# Example integration in a FastAPI endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.core.auth import get_current_customer
from app.db.schemas.connection import get_supabase_client
from app.models.car_media import CarMediaCreate, CarMediaListResponse, CarMediaUpdate
from app.models.customer import Customer
from app.services.car_media import CarMediaService

router = APIRouter(prefix="/api/v1/cars/{car_id}/media", tags=["car_media"])


@router.post("/", response_model=CarMedia)
async def create_car_media(
    car_id: int,
    media_data: CarMediaCreate,
    current_customer: Customer = Depends(get_current_customer),
    supabase = Depends(get_supabase_client),
):
    '''Create new media for a car.'''
    media_service = CarMediaService(supabase)
    
    # Ensure car_id and customer_id match
    media_data.car_id = car_id
    media_data.customer_id = current_customer.id
    
    return await media_service.create_media(media_data)


@router.get("/", response_model=CarMediaListResponse)
async def get_car_media(
    car_id: int,
    include_inactive: bool = False,
    current_customer: Customer = Depends(get_current_customer),
    supabase = Depends(get_supabase_client),
):
    '''Get all media for a car.'''
    media_service = CarMediaService(supabase)
    return await media_service.get_car_media(
        car_id, current_customer.id, include_inactive
    )


@router.patch("/{media_id}", response_model=CarMedia)
async def update_car_media(
    car_id: int,
    media_id: UUID,
    update_data: CarMediaUpdate,
    current_customer: Customer = Depends(get_current_customer),
    supabase = Depends(get_supabase_client),
):
    '''Update media metadata.'''
    media_service = CarMediaService(supabase)
    updated = await media_service.update_media(
        media_id, current_customer.id, update_data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Media not found")
    return updated


@router.post("/{media_id}/set-primary")
async def set_primary_image(
    car_id: int,
    media_id: UUID,
    current_customer: Customer = Depends(get_current_customer),
    supabase = Depends(get_supabase_client),
):
    '''Set media as primary image for the car.'''
    media_service = CarMediaService(supabase)
    success = await media_service.set_primary_image(
        media_id, car_id, current_customer.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"success": True}


@router.delete("/{media_id}")
async def delete_car_media(
    car_id: int,
    media_id: UUID,
    permanent: bool = False,
    current_customer: Customer = Depends(get_current_customer),
    supabase = Depends(get_supabase_client),
):
    '''Delete media (soft delete by default, permanent if specified).'''
    media_service = CarMediaService(supabase)
    
    if permanent:
        success = await media_service.hard_delete_media(media_id, current_customer.id)
    else:
        success = await media_service.delete_media(media_id, current_customer.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"success": True}
"""

if __name__ == "__main__":
    asyncio.run(main())
