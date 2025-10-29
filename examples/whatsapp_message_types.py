"""
Examples of using WhatsAppMessageType enum with WhatsAppMessageProcessor.

This file demonstrates how to use the new enum-based message type system
for better type safety and maintainability.
"""

from app.services.whatsapp import (
    WhatsAppMessageProcessor,
    WhatsAppMessageType,
    WhatsAppService,
    create_default_message_processor,
)


def example_default_processor():
    """Example: Using the default processor (text messages only)."""
    # Default processor handles only text messages
    service = create_default_message_processor()
    print(f"Default processor supports: {service.supported_message_types}")
    # Output: Default processor supports: {<WhatsAppMessageType.TEXT: 'text'>}


def example_text_only_processor():
    """Example: Create a text-only processor explicitly."""
    processor = WhatsAppMessageProcessor(
        supported_message_types={WhatsAppMessageType.TEXT}
    )

    print("Text-only processor:")
    # True
    print(f"Supports text: {processor.should_process_message('text')}")
    # False
    print(f"Supports image: {processor.should_process_message('image')}")
    # False
    print(f"Supports video: {processor.should_process_message('video')}")


def example_multimedia_processor():
    """Example: Create a processor that handles multiple message types."""
    processor = WhatsAppMessageProcessor(
        supported_message_types={
            WhatsAppMessageType.TEXT,
            WhatsAppMessageType.IMAGE,
            WhatsAppMessageType.VIDEO,
            WhatsAppMessageType.AUDIO,
            WhatsAppMessageType.DOCUMENT,
        }
    )

    print("Multimedia processor:")
    # True
    print(f"Supports text: {processor.should_process_message('text')}")
    # True
    print(f"Supports image: {processor.should_process_message('image')}")
    # True
    print(f"Supports video: {processor.should_process_message('video')}")
    # True
    print(f"Supports audio: {processor.should_process_message('audio')}")
    # True
    print(f"Supports document: {processor.should_process_message('document')}")
    # False
    print(f"Supports sticker: {processor.should_process_message('sticker')}")


def example_all_message_types():
    """Example: Show all available message types."""
    print("All available WhatsApp message types:")
    for msg_type in WhatsAppMessageType:
        print(f"  - {msg_type.name}: '{msg_type.value}'")


def example_service_with_custom_processor():
    """Example: Create a WhatsApp service with custom message processor."""
    # Create custom processor for text and media
    custom_processor = WhatsAppMessageProcessor(
        supported_message_types={
            WhatsAppMessageType.TEXT,
            WhatsAppMessageType.IMAGE,
            WhatsAppMessageType.VIDEO,
        }
    )

    # Create service with custom processor
    service = WhatsAppService(message_processor=custom_processor)

    print(
        f"Created service with processor supporting: {custom_processor.supported_message_types}"
    )
    return service


if __name__ == "__main__":
    print("=== WhatsApp Message Type Examples ===\n")

    example_all_message_types()
    print()

    example_default_processor()
    print()

    example_text_only_processor()
    print()

    example_multimedia_processor()
    print()

    example_service_with_custom_processor()
