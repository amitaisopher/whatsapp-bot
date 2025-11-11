# Media Management CLI Tool

A command-line interface tool for managing car media in the WhatsApp Chatbot system.

## Features

- ✅ List all customers with names, IDs, and statuses
- ✅ List all cars associated with a customer
- ✅ List all media items for a car
- ✅ Create new media items with validation
- ✅ Delete media (soft or hard delete)
- ✅ Set primary images for cars
- ✅ Interactive mode for easier data entry
- ✅ Beautiful tabular output with rich formatting
- ✅ Comprehensive error handling and validation

## Installation

The required dependencies are already in `pyproject.toml`:

```bash
uv pip install typer rich
```

Or if you prefer pip:

```bash
pip install typer rich
```

## Usage

Make sure your environment variables are set (`.env.development` or `.env.production`):

```bash
export ENVIRONMENT=development  # or production
export SUPABASE_URL=your_supabase_url
export SUPABASE_KEY=your_supabase_key
```

### List All Customers

Display all customers with their IDs, names, emails, statuses, and creation dates:

```bash
python manage_media.py list-customers
```

**Output:**
```
                                          Customers                                          
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ ID                                   ┃ Name       ┃ Email           ┃  Status ┃ Created At       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ 12345678-1234-5678-1234-567812345678 │ ABC Motors │ abc@example.com │ ✓ Active│ 2024-01-15 10:30 │
│ 87654321-4321-8765-4321-876543218765 │ XYZ Auto   │ xyz@example.com │ ✗ Inactive│ 2024-02-20 14:15│
└──────────────────────────────────────┴────────────┴─────────────────┴─────────┴──────────────────┘

Total customers: 2
```

### List Cars for a Customer

Display all cars associated with a specific customer:

```bash
python manage_media.py list-cars --customer-id "12345678-1234-5678-1234-567812345678"
```

**Shorthand:**
```bash
python manage_media.py list-cars -c "12345678-1234-5678-1234-567812345678"
```

**Output:**
```
Customer: ABC Motors
Customer ID: 12345678-1234-5678-1234-567812345678

                                                    Cars                                                    
┏━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ID ┃ Manufacturer ┃ Model    ┃ Year ┃ Chassis Number┃ Price (USD) ┃ Mileage (km)┃
┡━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│  1 │ Toyota       │ Camry    │ 2020 │ ABC123XYZ     │ $25,000.00  │ 45,000      │
│  2 │ Honda        │ Accord   │ 2021 │ DEF456UVW     │ $28,500.00  │ 32,000      │
└────┴──────────────┴──────────┴──────┴───────────────┴─────────────┴─────────────┘

Total cars: 2
```

### List Media for a Car

Display all media items for a specific car:

```bash
python manage_media.py list-media --customer-id "12345678-1234-5678-1234-567812345678" --car-id 1
```

**Shorthand:**
```bash
python manage_media.py list-media -c "12345678-1234-5678-1234-567812345678" -i 1
```

**Include inactive media:**
```bash
python manage_media.py list-media -c "UUID" -i 1 --include-inactive
```

**Output:**
```
Car: Toyota Camry (2020)
Car ID: 1

                                              Car Media                                              
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ ID                                   ┃ Type  ┃ URL                     ┃ File Name  ┃ Order ┃ Primary ┃ Active ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ 11111111-1111-1111-1111-111111111111 │ image │ https://cdn.com/car.jpg │ car_front  │   0   │    ★    │   ✓    │
│ 22222222-2222-2222-2222-222222222222 │ image │ https://cdn.com/side... │ car_side   │   1   │         │   ✓    │
│ 33333333-3333-3333-3333-333333333333 │ video │ https://cdn.com/tour... │ car_tour   │   2   │         │   ✓    │
└──────────────────────────────────────┴───────┴─────────────────────────┴────────────┴───────┴─────────┴────────┘

Summary:
  Images: 2
  Videos: 1
  Documents: 0
  Total: 3

Primary Image: car_front
```

### Create/Upsert Media

Create a new media item for a car:

```bash
python manage_media.py upsert-media \
  --customer-id "12345678-1234-5678-1234-567812345678" \
  --car-id 1 \
  --url "https://res.cloudinary.com/demo/car_front.jpg" \
  --type image \
  --provider cloudinary \
  --file-name "car_front.jpg" \
  --mime-type "image/jpeg" \
  --alt-text "Front view of the car" \
  --width 1920 \
  --height 1080 \
  --order 0 \
  --primary
```

**Shorthand:**
```bash
python manage_media.py upsert-media \
  -c "UUID" \
  -i 1 \
  -u "https://cdn.com/car.jpg" \
  -t image \
  -p cloudinary \
  --primary
```

**Interactive mode (easier):**
```bash
python manage_media.py upsert-media \
  -c "12345678-1234-5678-1234-567812345678" \
  -i 1 \
  --interactive
```

In interactive mode, you'll be prompted for each field:
```
Interactive Media Creation

Media URL: https://cdn.com/car.jpg
Media type (image/video/document/three_sixty_view/thumbnail) [image]: image
Storage provider (cloudinary/s3/local/supabase) [cloudinary]: cloudinary
File name (optional): car_front.jpg
MIME type (optional): image/jpeg
Alternative text (optional): Front view of the car
Width in pixels (optional): 1920
Height in pixels (optional): 1080
Display order [0]: 0
Set as primary image? [y/n] (n): y
```

**Options:**
- `--customer-id, -c`: Customer UUID (required)
- `--car-id, -i`: Car ID (required)
- `--url, -u`: Media URL (required)
- `--type, -t`: Media type (image, video, document, three_sixty_view, thumbnail)
- `--provider, -p`: Storage provider (cloudinary, s3, local, supabase)
- `--file-name, -f`: File name
- `--mime-type, -m`: MIME type (e.g., image/jpeg, video/mp4)
- `--alt-text, -a`: Alternative text for accessibility
- `--width, -w`: Image width in pixels
- `--height, -h`: Image height in pixels
- `--order, -o`: Display order (default: 0)
- `--primary`: Set as primary image
- `--interactive`: Interactive mode with prompts

### Delete Media

**Soft delete (recommended - deactivates media):**
```bash
python manage_media.py delete-media \
  --customer-id "12345678-1234-5678-1234-567812345678" \
  --media-id "11111111-1111-1111-1111-111111111111"
```

**Hard delete (permanent):**
```bash
python manage_media.py delete-media \
  --customer-id "UUID" \
  --media-id "MEDIA-UUID" \
  --permanent
```

**Shorthand:**
```bash
python manage_media.py delete-media -c "UUID" -m "MEDIA-UUID"
```

### Set Primary Image

Set a specific media item as the primary image for a car:

```bash
python manage_media.py set-primary \
  --customer-id "12345678-1234-5678-1234-567812345678" \
  --car-id 1 \
  --media-id "11111111-1111-1111-1111-111111111111"
```

**Shorthand:**
```bash
python manage_media.py set-primary -c "UUID" -i 1 -m "MEDIA-UUID"
```

## Command Reference

### Global Options

All commands support `--help` to see detailed information:

```bash
python manage_media.py --help
python manage_media.py list-customers --help
python manage_media.py upsert-media --help
```

### Commands

| Command | Description |
|---------|-------------|
| `list-customers` | List all customers |
| `list-cars` | List cars for a customer |
| `list-media` | List media for a car |
| `upsert-media` | Create new media for a car |
| `delete-media` | Delete media (soft or hard) |
| `set-primary` | Set primary image for a car |

## Validation & Safety

The tool includes comprehensive validation:

- ✅ **UUID Validation**: Validates all UUID inputs
- ✅ **Positive Integer Validation**: Ensures car IDs are positive
- ✅ **URL Format Validation**: Checks URL starts with http://, https://, or /
- ✅ **Customer Verification**: Verifies customer exists before operations
- ✅ **Car Ownership Verification**: Ensures car belongs to customer
- ✅ **Media Existence Check**: Verifies media exists before deletion
- ✅ **Confirmation Prompts**: Asks for confirmation on destructive operations
- ✅ **Error Handling**: Comprehensive error messages and exit codes

## Error Handling

The tool provides clear error messages:

```bash
# Invalid UUID
Error: Invalid UUID format: not-a-uuid

# Customer not found
Error: Customer with ID 12345678-1234-5678-1234-567812345678 not found.

# Car not found or doesn't belong to customer
Error: Car with ID 999 not found for this customer.

# Database connection issues
Error connecting to database: SUPABASE_URL not configured
```

## Examples

### Complete Workflow

```bash
# 1. List all customers to find the UUID
python manage_media.py list-customers

# 2. List cars for a customer
python manage_media.py list-cars -c "12345678-1234-5678-1234-567812345678"

# 3. Add images for a car (interactive mode)
python manage_media.py upsert-media -c "UUID" -i 1 --interactive

# 4. List media to verify
python manage_media.py list-media -c "UUID" -i 1

# 5. Set a different primary image
python manage_media.py set-primary -c "UUID" -i 1 -m "MEDIA-UUID"

# 6. Delete old media (soft delete)
python manage_media.py delete-media -c "UUID" -m "OLD-MEDIA-UUID"
```

### Bulk Upload Images

Create a script to bulk upload images:

```bash
#!/bin/bash
CUSTOMER_ID="12345678-1234-5678-1234-567812345678"
CAR_ID=1

# Array of image URLs
IMAGES=(
  "https://cdn.com/car_front.jpg"
  "https://cdn.com/car_side.jpg"
  "https://cdn.com/car_rear.jpg"
  "https://cdn.com/car_interior.jpg"
)

# Upload each image
for i in "${!IMAGES[@]}"; do
  python manage_media.py upsert-media \
    -c "$CUSTOMER_ID" \
    -i "$CAR_ID" \
    -u "${IMAGES[$i]}" \
    -t image \
    -o "$i" \
    $([ $i -eq 0 ] && echo "--primary")
done

echo "Uploaded ${#IMAGES[@]} images!"
```

## Troubleshooting

### Environment Variables Not Set

```bash
Error connecting to database: SUPABASE_URL not configured
```

**Solution:** Set environment variables:
```bash
export ENVIRONMENT=development
export SUPABASE_URL=your_url
export SUPABASE_KEY=your_key
```

Or use a `.env` file and load it:
```bash
source .env.development
python manage_media.py list-customers
```

### Import Errors

```bash
ModuleNotFoundError: No module named 'typer'
```

**Solution:** Install dependencies:
```bash
uv pip install typer rich
# or
pip install typer rich
```

### Permission Denied

```bash
bash: ./manage_media.py: Permission denied
```

**Solution:** Make script executable:
```bash
chmod +x manage_media.py
```

## Technical Details

### Dependencies

- **typer**: CLI framework with type hints
- **rich**: Beautiful terminal formatting
- **supabase-py**: Database client
- **pydantic**: Data validation

### Database Tables

The tool interacts with:
- `customers` - Customer information
- `cars` - Car inventory
- `car_media` - Media items (images, videos, etc.)

### Row-Level Security (RLS)

All operations respect Supabase RLS policies, ensuring:
- Customers can only access their own data
- Media operations are scoped to customer ownership
- Foreign key constraints are enforced

## Advanced Usage

### Scripting

The tool returns appropriate exit codes:
- `0`: Success
- `1`: Error

Use in scripts:

```bash
#!/bin/bash
if python manage_media.py list-cars -c "UUID" > /dev/null 2>&1; then
  echo "Customer has cars"
else
  echo "No cars found or error occurred"
fi
```

### JSON Output (Future Enhancement)

Currently outputs rich tables. To add JSON support:

```python
# Add --format option
@app.command()
def list_customers(
    format: str = typer.Option("table", "--format", "-f", help="Output format")
):
    # ... existing code ...
    if format == "json":
        import json
        print(json.dumps(response.data, indent=2))
```

## Related Documentation

- [Car Media Documentation](docs/CAR_MEDIA.md)
- [Database Schema](docs/DATABASE.md)
- [API Documentation](docs/API.md)

## Support

For issues or questions:
1. Check error messages for specific guidance
2. Review validation requirements
3. Verify environment variables are set
4. Check database connectivity
5. Review RLS policies for permission issues
