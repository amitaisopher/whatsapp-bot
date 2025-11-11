# Car Media Management

This feature allows you to store and manage multiple images, videos, and documents for each car in your inventory.

## Overview

The car media system provides:
- Multiple media types: images, videos, documents, 360° views, thumbnails
- Storage provider flexibility: Cloudinary, S3, Supabase, local storage
- Primary image designation for each car
- Display order management
- Soft delete capability (media can be deactivated without permanent deletion)
- Row-Level Security (RLS) for multi-tenant isolation
- Enhanced semantic search that includes image data

## Database Schema

### Tables

#### `car_media` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `car_id` | INTEGER | Foreign key to `cars` table (CASCADE delete) |
| `customer_id` | UUID | Foreign key to `customers` table (CASCADE delete) |
| `media_type` | media_type enum | Type of media (image/video/document/three_sixty_view/thumbnail) |
| `url` | VARCHAR(2048) | URL to the media file |
| `storage_provider` | VARCHAR(50) | Storage provider (cloudinary/s3/local/supabase) |
| `file_name` | VARCHAR(255) | Original filename |
| `mime_type` | VARCHAR(100) | MIME type (e.g., image/jpeg, video/mp4) |
| `file_size_bytes` | BIGINT | File size in bytes |
| `width` | INTEGER | Image/video width in pixels |
| `height` | INTEGER | Image/video height in pixels |
| `alt_text` | TEXT | Alternative text for accessibility |
| `display_order` | INTEGER | Order for displaying media (0-based) |
| `is_primary` | BOOLEAN | Whether this is the primary image for the car |
| `is_active` | BOOLEAN | Whether the media is active (soft delete) |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### Enums

#### `media_type` Enum

- `image` - Regular images
- `video` - Video files
- `document` - PDF, documents, etc.
- `three_sixty_view` - 360° view images/videos
- `thumbnail` - Thumbnail images

### Indexes

- `idx_car_media_car_id` - Fast lookups by car
- `idx_car_media_customer_id` - Fast lookups by customer
- `idx_car_media_type` - Fast filtering by media type
- `idx_car_media_primary` - Fast lookups for primary images
- `idx_car_media_active` - Fast filtering by active status

### Row-Level Security (RLS)

RLS policies ensure customers can only access their own media:
- `select_own_car_media` - Can view own media
- `insert_own_car_media` - Can create media for own cars
- `update_own_car_media` - Can update own media
- `delete_own_car_media` - Can delete own media

### CASCADE Deletes

Media is automatically deleted when:
- The associated car is deleted
- The associated customer is deleted

## Installation

### 1. Run Migration

Execute the migration file to set up the database:

```bash
# Using psql
psql -h YOUR_HOST -U YOUR_USER -d YOUR_DB -f migrations/001_add_car_media.sql

# Or using Supabase CLI
supabase db push
```

### 2. Verify Installation

Check that the table and policies were created:

```sql
-- Check table exists
SELECT * FROM car_media LIMIT 1;

-- Check enum exists
SELECT enum_range(NULL::media_type);

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'car_media';
```

## Usage

### Basic Usage

```python
from uuid import UUID
from supabase import create_client

from app.models.car_media import CarMediaCreate, MediaType, StorageProvider
from app.services.car_media import CarMediaService

# Initialize service
supabase = create_client(supabase_url, supabase_key)
media_service = CarMediaService(supabase)

# Create a new image
new_image = CarMediaCreate(
    car_id=1,
    customer_id=UUID("..."),
    media_type=MediaType.IMAGE,
    url="https://res.cloudinary.com/example/car_front.jpg",
    storage_provider=StorageProvider.CLOUDINARY,
    file_name="car_front.jpg",
    mime_type="image/jpeg",
    width=1920,
    height=1080,
    alt_text="Front view of the car",
    is_primary=True,
)

created = await media_service.create_media(new_image)
```

### Get All Media for a Car

```python
# Get organized media list
car_media = await media_service.get_car_media(
    car_id=1,
    customer_id=UUID("..."),
)

print(f"Total: {car_media.total_count}")
print(f"Images: {len(car_media.images)}")
print(f"Videos: {len(car_media.videos)}")
print(f"Primary image: {car_media.primary_image.url}")
```

### Bulk Create Media

```python
images_to_create = [
    CarMediaCreate(
        car_id=1,
        customer_id=UUID("..."),
        media_type=MediaType.IMAGE,
        url=f"https://example.com/car_{view}.jpg",
        file_name=f"car_{view}.jpg",
        display_order=idx,
    )
    for idx, view in enumerate(["front", "side", "rear", "interior"])
]

created_images = await media_service.bulk_create_media(images_to_create)
```

### Update Media

```python
from app.models.car_media import CarMediaUpdate

update_data = CarMediaUpdate(
    alt_text="Updated description",
    display_order=5,
)

updated = await media_service.update_media(
    media_id=UUID("..."),
    customer_id=UUID("..."),
    update_data=update_data,
)
```

### Set Primary Image

```python
success = await media_service.set_primary_image(
    media_id=UUID("..."),
    car_id=1,
    customer_id=UUID("..."),
)
```

### Reorder Media

```python
media_order = [
    {"id": "uuid-1", "display_order": 0},
    {"id": "uuid-2", "display_order": 1},
    {"id": "uuid-3", "display_order": 2},
]

success = await media_service.reorder_media(
    car_id=1,
    customer_id=UUID("..."),
    media_order=media_order,
)
```

### Delete Media

```python
# Soft delete (recommended)
success = await media_service.delete_media(
    media_id=UUID("..."),
    customer_id=UUID("..."),
)

# Hard delete (permanent)
success = await media_service.hard_delete_media(
    media_id=UUID("..."),
    customer_id=UUID("..."),
)
```

## API Integration Example

See `examples/car_media_usage.py` for a complete FastAPI router implementation.

```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/cars/{car_id}/media")

@router.post("/")
async def create_car_media(
    car_id: int,
    media_data: CarMediaCreate,
    current_customer: Customer = Depends(get_current_customer),
    supabase = Depends(get_supabase_client),
):
    media_service = CarMediaService(supabase)
    media_data.car_id = car_id
    media_data.customer_id = current_customer.id
    return await media_service.create_media(media_data)
```

## Enhanced Semantic Search

The migration includes an enhanced `semantic_search_cars_with_images` function that incorporates image data:

```sql
SELECT * FROM semantic_search_cars_with_images(
    p_customer_id := 'YOUR-UUID',
    p_query_embedding := YOUR_EMBEDDING_VECTOR,
    p_match_threshold := 0.7,
    p_match_count := 10
);
```

Returns car details including:
- Primary image URL
- Total image count
- Total media count

## Best Practices

### 1. Primary Images

- Always set at least one image as primary
- Use high-quality images for primary
- Update primary image when better photos are available

### 2. Display Order

- Start from 0 for consistent ordering
- Use consistent increments (0, 1, 2, 3...)
- Reorder when adding/removing images

### 3. Media Types

- Use `image` for standard photos
- Use `three_sixty_view` for 360° tours
- Use `thumbnail` for preview images
- Use `video` for walkaround videos
- Use `document` for brochures, specs, etc.

### 4. Storage Providers

- Cloudinary: Best for image transformations
- S3: Best for large files, videos
- Supabase: Integrated storage with RLS
- Local: Development only

### 5. Soft Deletes

- Use soft delete by default (keeps history)
- Hard delete only when necessary (GDPR, storage limits)
- Include inactive media for admin views

### 6. File Metadata

- Always store `width` and `height` for images
- Always store `mime_type` for proper content handling
- Always store `file_size_bytes` for quota tracking
- Use `alt_text` for accessibility

### 7. Performance

- Leverage indexes for filtering
- Use `display_order` for efficient sorting
- Cache primary images at application level
- Use CDN for media URLs

## Troubleshooting

### Media Not Appearing

1. Check RLS policies are enabled: `SELECT rls FROM pg_tables WHERE tablename = 'car_media'`
2. Verify customer_id matches authenticated user
3. Check `is_active = true` filter

### Primary Image Not Set

1. Query all images: `SELECT * FROM car_media WHERE car_id = X AND media_type = 'image'`
2. Set primary manually: `UPDATE car_media SET is_primary = true WHERE id = ...`

### Slow Queries

1. Check indexes: `SELECT * FROM pg_indexes WHERE tablename = 'car_media'`
2. Analyze query plan: `EXPLAIN ANALYZE SELECT * FROM car_media WHERE ...`
3. Consider adding composite indexes for common filters

## Migration Rollback

To rollback this migration:

```sql
-- Drop the enhanced search function
DROP FUNCTION IF EXISTS semantic_search_cars_with_images;

-- Drop the table (CASCADE will drop constraints)
DROP TABLE IF EXISTS car_media CASCADE;

-- Drop the enum type
DROP TYPE IF EXISTS media_type;
```

## Future Enhancements

- Image transformation API (resize, crop, format)
- Automatic thumbnail generation
- Video transcoding support
- Image recognition/tagging
- Duplicate detection
- Bulk upload API
- Media analytics (views, clicks)
