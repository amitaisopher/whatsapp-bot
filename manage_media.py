#!/usr/bin/env python3
"""
Media Management CLI Tool

This script provides utilities to:
1. List all customers with their names, IDs, and statuses
2. List all cars associated with a customer
3. Upsert media items for a car

Usage:
    python manage_media.py list-customers
    python manage_media.py list-cars --customer-id <UUID>
    python manage_media.py upsert-media --customer-id <UUID> --car-id <ID> --url <URL> [options]
"""

import asyncio
import sys
from datetime import datetime
from typing import Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from supabase import Client

from app.core.config import settings
from app.models.car_media import (
    CarMediaCreate,
    MediaType,
    StorageProvider,
)
from app.services.car_media import CarMediaService
from app.services.database import get_supabase_client

# Initialize CLI app and console
app = typer.Typer(help="Car Media Management CLI")
console = Console()


def get_client() -> Client:
    """Get Supabase client with error handling."""
    try:
        return get_supabase_client()
    except Exception as e:
        console.print(f"[red]Error connecting to database: {e}[/red]")
        raise typer.Exit(code=1)


def validate_uuid(value: str) -> UUID:
    """Validate UUID format."""
    try:
        return UUID(value)
    except ValueError:
        console.print(f"[red]Error: Invalid UUID format: {value}[/red]")
        raise typer.Exit(code=1)


def validate_positive_int(value: int, field_name: str) -> int:
    """Validate positive integer."""
    if value <= 0:
        console.print(f"[red]Error: {field_name} must be a positive integer[/red]")
        raise typer.Exit(code=1)
    return value


@app.command("list-customers")
def list_customers():
    """List all customers with their names, IDs, and statuses."""
    try:
        supabase = get_client()
        
        # Query customers
        response = supabase.table("customers").select("*").order("name").execute()
        
        if not response.data:
            console.print("[yellow]No customers found.[/yellow]")
            return
        
        # Create table
        table = Table(title="Customers", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=36)
        table.add_column("Name", style="green")
        table.add_column("Email", style="blue")
        table.add_column("Status", justify="center")
        table.add_column("Created At", style="dim")
        
        # Add rows
        for customer in response.data:
            status = "✓ Active" if customer.get("is_active", False) else "✗ Inactive"
            status_style = "green" if customer.get("is_active", False) else "red"
            
            created_at = customer.get("created_at", "")
            if created_at:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
            
            table.add_row(
                str(customer.get("id", "")),
                customer.get("name", "N/A"),
                customer.get("contact_email", "N/A"),
                f"[{status_style}]{status}[/{status_style}]",
                created_at,
            )
        
        console.print(table)
        console.print(f"\n[bold]Total customers: {len(response.data)}[/bold]")
        
    except Exception as e:
        console.print(f"[red]Error listing customers: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("list-cars")
def list_cars(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Customer UUID"),
):
    """List all cars associated with a customer."""
    try:
        # Validate customer ID
        customer_uuid = validate_uuid(customer_id)
        
        supabase = get_client()
        
        # Verify customer exists
        customer_response = (
            supabase.table("customers")
            .select("*")
            .eq("id", str(customer_uuid))
            .execute()
        )
        
        if not customer_response.data:
            console.print(f"[red]Error: Customer with ID {customer_id} not found.[/red]")
            raise typer.Exit(code=1)
        
        customer = customer_response.data[0]
        console.print(f"\n[bold cyan]Customer:[/bold cyan] {customer.get('name', 'N/A')}")
        console.print(f"[bold cyan]Customer ID:[/bold cyan] {customer_id}\n")
        
        # Query cars
        response = (
            supabase.table("cars")
            .select("*")
            .eq("customer_id", str(customer_uuid))
            .order("id")
            .execute()
        )
        
        if not response.data:
            console.print("[yellow]No cars found for this customer.[/yellow]")
            return
        
        # Create table
        table = Table(title="Cars", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Manufacturer", style="green")
        table.add_column("Model", style="blue")
        table.add_column("Year", justify="center")
        table.add_column("Chassis Number", style="yellow")
        table.add_column("Price (USD)", justify="right")
        table.add_column("Mileage (km)", justify="right")
        
        # Add rows
        for car in response.data:
            table.add_row(
                str(car.get("id", "")),
                car.get("make", "N/A"),
                car.get("model", "N/A"),
                str(car.get("model_year", "N/A")),
                car.get("chassis_number", "N/A"),
                f"${car.get('price_usd', 0):,.2f}",
                f"{car.get('mileage_km', 0):,}",
            )
        
        console.print(table)
        console.print(f"\n[bold]Total cars: {len(response.data)}[/bold]")
        
    except Exception as e:
        console.print(f"[red]Error listing cars: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("list-media")
def list_media(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Customer UUID"),
    car_id: int = typer.Option(..., "--car-id", "-i", help="Car ID"),
    include_inactive: bool = typer.Option(False, "--include-inactive", help="Include inactive media"),
):
    """List all media for a specific car."""
    try:
        # Validate inputs
        customer_uuid = validate_uuid(customer_id)
        validate_positive_int(car_id, "Car ID")
        
        supabase = get_client()
        media_service = CarMediaService(supabase)
        
        # Verify car exists and belongs to customer
        car_response = (
            supabase.table("cars")
            .select("*")
            .eq("id", car_id)
            .eq("customer_id", str(customer_uuid))
            .execute()
        )
        
        if not car_response.data:
            console.print(f"[red]Error: Car with ID {car_id} not found for this customer.[/red]")
            raise typer.Exit(code=1)
        
        car = car_response.data[0]
        console.print(f"\n[bold cyan]Car:[/bold cyan] {car.get('make')} {car.get('model')} ({car.get('model_year')})")
        console.print(f"[bold cyan]Car ID:[/bold cyan] {car_id}\n")
        
        # Get media
        car_media = asyncio.run(
            media_service.get_car_media(car_id, customer_uuid, include_inactive)
        )
        
        if car_media.total_count == 0:
            console.print("[yellow]No media found for this car.[/yellow]")
            return
        
        # Create table
        table = Table(title="Car Media", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=36)
        table.add_column("Type", style="green")
        table.add_column("URL", style="blue", max_width=50)
        table.add_column("File Name", style="yellow")
        table.add_column("Order", justify="center")
        table.add_column("Primary", justify="center")
        table.add_column("Active", justify="center")
        
        # Combine all media
        all_media = car_media.images + car_media.videos + car_media.documents
        all_media.sort(key=lambda x: (x.display_order, x.created_at))
        
        # Add rows
        for media in all_media:
            primary_icon = "★" if media.is_primary else ""
            active_icon = "✓" if media.is_active else "✗"
            active_color = "green" if media.is_active else "red"
            
            table.add_row(
                str(media.id),
                media.media_type.value,
                media.url[:47] + "..." if len(media.url) > 50 else media.url,
                media.file_name or "N/A",
                str(media.display_order),
                f"[yellow]{primary_icon}[/yellow]",
                f"[{active_color}]{active_icon}[/{active_color}]",
            )
        
        console.print(table)
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Images: {len(car_media.images)}")
        console.print(f"  Videos: {len(car_media.videos)}")
        console.print(f"  Documents: {len(car_media.documents)}")
        console.print(f"  Total: {car_media.total_count}")
        
        if car_media.primary_image:
            console.print(f"\n[bold green]Primary Image:[/bold green] {car_media.primary_image.file_name or car_media.primary_image.url}")
        
    except Exception as e:
        console.print(f"[red]Error listing media: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("upsert-media")
def upsert_media(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Customer UUID"),
    car_id: int = typer.Option(..., "--car-id", "-i", help="Car ID"),
    url: str = typer.Option(..., "--url", "-u", help="Media URL"),
    media_type: MediaType = typer.Option(MediaType.IMAGE, "--type", "-t", help="Media type"),
    storage_provider: StorageProvider = typer.Option(
        StorageProvider.CLOUDINARY, "--provider", "-p", help="Storage provider"
    ),
    file_name: Optional[str] = typer.Option(None, "--file-name", "-f", help="File name"),
    mime_type: Optional[str] = typer.Option(None, "--mime-type", "-m", help="MIME type"),
    alt_text: Optional[str] = typer.Option(None, "--alt-text", "-a", help="Alternative text"),
    width: Optional[int] = typer.Option(None, "--width", "-w", help="Image width"),
    height: Optional[int] = typer.Option(None, "--height", "-h", help="Image height"),
    display_order: int = typer.Option(0, "--order", "-o", help="Display order"),
    is_primary: bool = typer.Option(False, "--primary", help="Set as primary image"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive mode"),
):
    """
    Upsert (create or update) media for a car.
    
    Examples:
        # Create a new image
        python manage_media.py upsert-media -c UUID -i 1 -u https://example.com/car.jpg --primary
        
        # Interactive mode
        python manage_media.py upsert-media -c UUID -i 1 --interactive
    """
    try:
        # Validate inputs
        customer_uuid = validate_uuid(customer_id)
        validate_positive_int(car_id, "Car ID")
        
        supabase = get_client()
        media_service = CarMediaService(supabase)
        
        # Verify car exists and belongs to customer
        car_response = (
            supabase.table("cars")
            .select("*")
            .eq("id", car_id)
            .eq("customer_id", str(customer_uuid))
            .execute()
        )
        
        if not car_response.data:
            console.print(f"[red]Error: Car with ID {car_id} not found for this customer.[/red]")
            raise typer.Exit(code=1)
        
        car = car_response.data[0]
        console.print(f"\n[bold cyan]Car:[/bold cyan] {car.get('make')} {car.get('model')} ({car.get('model_year')})")
        
        # Interactive mode
        if interactive:
            console.print("\n[bold]Interactive Media Creation[/bold]\n")
            
            url = Prompt.ask("Media URL")
            
            media_type_choice = Prompt.ask(
                "Media type",
                choices=[t.value for t in MediaType],
                default=MediaType.IMAGE.value,
            )
            media_type = MediaType(media_type_choice)
            
            storage_provider_choice = Prompt.ask(
                "Storage provider",
                choices=[p.value for p in StorageProvider],
                default=StorageProvider.CLOUDINARY.value,
            )
            storage_provider = StorageProvider(storage_provider_choice)
            
            file_name = Prompt.ask("File name (optional)", default="") or None
            mime_type = Prompt.ask("MIME type (optional)", default="") or None
            alt_text = Prompt.ask("Alternative text (optional)", default="") or None
            
            if media_type == MediaType.IMAGE:
                width_str = Prompt.ask("Width in pixels (optional)", default="")
                height_str = Prompt.ask("Height in pixels (optional)", default="")
                width = int(width_str) if width_str else None
                height = int(height_str) if height_str else None
            else:
                width = None
                height = None
            
            display_order = int(Prompt.ask("Display order", default="0"))
            is_primary = Confirm.ask("Set as primary image?", default=False)
        
        # Validate URL format
        if not url.startswith(("http://", "https://", "/")):
            console.print("[red]Error: URL must start with http://, https://, or /[/red]")
            raise typer.Exit(code=1)
        
        # Create media object
        media_data = CarMediaCreate(
            car_id=car_id,
            customer_id=customer_uuid,
            media_type=media_type,
            url=url,
            storage_provider=storage_provider,
            file_name=file_name,
            mime_type=mime_type,
            alt_text=alt_text,
            width=width,
            height=height,
            display_order=display_order,
            is_primary=is_primary,
        )
        
        # Show summary
        console.print("\n[bold]Media Summary:[/bold]")
        console.print(f"  Type: {media_type.value}")
        console.print(f"  URL: {url}")
        console.print(f"  Storage: {storage_provider.value}")
        console.print(f"  Display Order: {display_order}")
        console.print(f"  Primary: {is_primary}")
        
        if not interactive:
            confirm = Confirm.ask("\nCreate this media?", default=True)
            if not confirm:
                console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        # Create media
        created_media = asyncio.run(media_service.create_media(media_data))
        
        console.print(f"\n[bold green]✓ Media created successfully![/bold green]")
        console.print(f"Media ID: {created_media.id}")
        
        # If set as primary, update other images
        if is_primary:
            asyncio.run(
                media_service.set_primary_image(created_media.id, car_id, customer_uuid)
            )
            console.print("[green]✓ Set as primary image[/green]")
        
    except Exception as e:
        console.print(f"[red]Error upserting media: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("delete-media")
def delete_media(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Customer UUID"),
    media_id: str = typer.Option(..., "--media-id", "-m", help="Media UUID"),
    permanent: bool = typer.Option(False, "--permanent", help="Permanently delete (default: soft delete)"),
):
    """Delete media (soft delete by default, permanent if specified)."""
    try:
        # Validate inputs
        customer_uuid = validate_uuid(customer_id)
        media_uuid = validate_uuid(media_id)
        
        supabase = get_client()
        media_service = CarMediaService(supabase)
        
        # Get media details before deletion
        media = asyncio.run(media_service.get_media_by_id(media_uuid, customer_uuid))
        
        if not media:
            console.print(f"[red]Error: Media with ID {media_id} not found.[/red]")
            raise typer.Exit(code=1)
        
        console.print(f"\n[bold]Media Details:[/bold]")
        console.print(f"  ID: {media.id}")
        console.print(f"  Type: {media.media_type.value}")
        console.print(f"  URL: {media.url}")
        console.print(f"  File: {media.file_name or 'N/A'}")
        
        delete_type = "permanently delete" if permanent else "soft delete (deactivate)"
        confirm = Confirm.ask(f"\n[red]Are you sure you want to {delete_type} this media?[/red]", default=False)
        
        if not confirm:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
        
        # Delete media
        if permanent:
            success = asyncio.run(media_service.hard_delete_media(media_uuid, customer_uuid))
            action = "permanently deleted"
        else:
            success = asyncio.run(media_service.delete_media(media_uuid, customer_uuid))
            action = "deactivated"
        
        if success:
            console.print(f"\n[bold green]✓ Media {action} successfully![/bold green]")
        else:
            console.print(f"[red]Error: Failed to delete media.[/red]")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]Error deleting media: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("set-primary")
def set_primary(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Customer UUID"),
    car_id: int = typer.Option(..., "--car-id", "-i", help="Car ID"),
    media_id: str = typer.Option(..., "--media-id", "-m", help="Media UUID"),
):
    """Set a media item as the primary image for a car."""
    try:
        # Validate inputs
        customer_uuid = validate_uuid(customer_id)
        media_uuid = validate_uuid(media_id)
        validate_positive_int(car_id, "Car ID")
        
        supabase = get_client()
        media_service = CarMediaService(supabase)
        
        # Verify media exists
        media = asyncio.run(media_service.get_media_by_id(media_uuid, customer_uuid))
        
        if not media:
            console.print(f"[red]Error: Media with ID {media_id} not found.[/red]")
            raise typer.Exit(code=1)
        
        if media.car_id != car_id:
            console.print(f"[red]Error: Media does not belong to car {car_id}.[/red]")
            raise typer.Exit(code=1)
        
        console.print(f"\n[bold]Setting as primary:[/bold]")
        console.print(f"  Media: {media.file_name or media.url}")
        console.print(f"  Type: {media.media_type.value}")
        
        # Set as primary
        success = asyncio.run(
            media_service.set_primary_image(media_uuid, car_id, customer_uuid)
        )
        
        if success:
            console.print(f"\n[bold green]✓ Media set as primary image successfully![/bold green]")
        else:
            console.print(f"[red]Error: Failed to set primary image.[/red]")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]Error setting primary image: {e}[/red]")
        raise typer.Exit(code=1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
