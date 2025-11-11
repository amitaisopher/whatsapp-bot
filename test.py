from app.core.config import get_settings
from app.services.whatsapp import get_whatsapp_service, WhatsAppService

settings = get_settings()
whatstapp_service = get_whatsapp_service()

async def send_test_image():
    try:
        response = await whatstapp_service.send_image(
            to="972526082002",
            image_url="https://i.imgur.com/Fh7XVYY.jpeg",
            caption="Here is an image for you!"
        )

        print("Image message sent successfully:", response)
    except Exception as e:
        print("Error sending image message:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_test_image())