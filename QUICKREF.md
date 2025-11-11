# Media Management CLI - Quick Reference

## Installation

```bash
# Dependencies already installed
uv pip install typer rich
```

## Quick Start

```bash
# Set environment (if not already set)
export ENVIRONMENT=development
export SUPABASE_URL=your_url
export SUPABASE_KEY=your_key

# List all customers
./media list-customers

# List cars for a customer
./media list-cars -c "CUSTOMER-UUID"

# Create media (interactive)
./media upsert-media -c "CUSTOMER-UUID" -i CAR-ID --interactive
```

## All Commands

### List Customers
```bash
./media list-customers
```
Shows: ID, Name, Email, Status, Created At

### List Cars
```bash
./media list-cars --customer-id "UUID"
./media list-cars -c "UUID"  # Short form
```
Shows: ID, Manufacturer, Model, Year, Chassis, Price, Mileage

### List Media
```bash
./media list-media --customer-id "UUID" --car-id ID
./media list-media -c "UUID" -i ID  # Short form
./media list-media -c "UUID" -i ID --include-inactive  # Include inactive
```
Shows: ID, Type, URL, File Name, Order, Primary, Active

### Create Media (Interactive)
```bash
./media upsert-media -c "UUID" -i ID --interactive
```
Prompts for: URL, type, provider, file name, dimensions, alt text, order, primary

### Create Media (Direct)
```bash
./media upsert-media \
  --customer-id "UUID" \
  --car-id ID \
  --url "https://cdn.com/car.jpg" \
  --type image \
  --provider cloudinary \
  --file-name "car_front.jpg" \
  --mime-type "image/jpeg" \
  --alt-text "Front view" \
  --width 1920 \
  --height 1080 \
  --order 0 \
  --primary
```

Short form:
```bash
./media upsert-media -c "UUID" -i ID -u "URL" -t image --primary
```

### Delete Media
```bash
# Soft delete (recommended)
./media delete-media --customer-id "UUID" --media-id "MEDIA-UUID"
./media delete-media -c "UUID" -m "MEDIA-UUID"  # Short form

# Hard delete (permanent)
./media delete-media -c "UUID" -m "MEDIA-UUID" --permanent
```

### Set Primary Image
```bash
./media set-primary --customer-id "UUID" --car-id ID --media-id "MEDIA-UUID"
./media set-primary -c "UUID" -i ID -m "MEDIA-UUID"  # Short form
```

## Media Types

- `image` - Photos
- `video` - Videos
- `document` - PDFs, documents
- `three_sixty_view` - 360° views
- `thumbnail` - Thumbnails

## Storage Providers

- `cloudinary` - Cloudinary
- `s3` - AWS S3
- `supabase` - Supabase Storage
- `local` - Local storage

## Options Reference

### Common Options
- `-c, --customer-id` - Customer UUID (required)
- `-i, --car-id` - Car ID (required for car operations)
- `-m, --media-id` - Media UUID (required for media operations)

### Media Options
- `-u, --url` - Media URL
- `-t, --type` - Media type (image/video/document/three_sixty_view/thumbnail)
- `-p, --provider` - Storage provider (cloudinary/s3/supabase/local)
- `-f, --file-name` - File name
- `-m, --mime-type` - MIME type (image/jpeg, video/mp4, etc.)
- `-a, --alt-text` - Alternative text for accessibility
- `-w, --width` - Image width in pixels
- `-h, --height` - Image height in pixels
- `-o, --order` - Display order (default: 0)
- `--primary` - Set as primary image
- `--interactive` - Interactive mode

### Other Options
- `--include-inactive` - Include inactive media in list
- `--permanent` - Permanently delete (hard delete)

## Common Workflows

### Setup New Car Media
```bash
# 1. Find customer
./media list-customers

# 2. Find car
./media list-cars -c "UUID"

# 3. Add images
./media upsert-media -c "UUID" -i 1 --interactive

# 4. Verify
./media list-media -c "UUID" -i 1
```

### Bulk Add Images
```bash
#!/bin/bash
CUSTOMER="12345678-1234-5678-1234-567812345678"
CAR=1

for i in {0..3}; do
  ./media upsert-media \
    -c "$CUSTOMER" \
    -i "$CAR" \
    -u "https://cdn.com/car_$i.jpg" \
    -o "$i" \
    $([ $i -eq 0 ] && echo "--primary")
done
```

### Replace Primary Image
```bash
# 1. List current media
./media list-media -c "UUID" -i 1

# 2. Upload new image
./media upsert-media -c "UUID" -i 1 -u "NEW-URL" --primary

# 3. Delete old image (optional)
./media delete-media -c "UUID" -m "OLD-MEDIA-UUID"
```

## Troubleshooting

### Environment Not Set
```bash
export ENVIRONMENT=development
export SUPABASE_URL=your_url
export SUPABASE_KEY=your_key
```

### Permission Denied
```bash
chmod +x media
```

### Module Not Found
```bash
uv pip install typer rich
```

### Use Virtual Environment
```bash
.venv/bin/python manage_media.py list-customers
```

## Help Commands

```bash
# Main help
./media --help

# Command-specific help
./media list-customers --help
./media list-cars --help
./media list-media --help
./media upsert-media --help
./media delete-media --help
./media set-primary --help
```

## Complete Documentation

- [docs/MEDIA_CLI.md](docs/MEDIA_CLI.md) - Full CLI documentation
- [docs/CAR_MEDIA.md](docs/CAR_MEDIA.md) - Car media system documentation
- [examples/car_media_usage.py](examples/car_media_usage.py) - Python API examples

## Tips

1. **Use interactive mode** when you're not sure about the options
2. **Use short forms** (-c, -i, -m) for faster typing
3. **Set primary image** when uploading the first image
4. **Soft delete first**, hard delete only if needed
5. **Check list-media** after operations to verify
6. **Use --help** to see all options for any command

## Exit Codes

- `0` - Success
- `1` - Error (check error message)
