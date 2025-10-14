# tasks.py
from httpx import AsyncClient
import asyncio

from app.core.redis import REDIS_SETTINGS
from app.services.whatsapp import WhatsAppService
from app.core.logging import get_application_logger


async def download_content(ctx, url):
    logger = ctx['logger']
    session: AsyncClient = ctx['session']
    # response = await session.get(url)
    # print(f'{url}: {response.text:.80}...')
    # return len(response.text)
    logger.info(f'Allegedly downloaded content from {url}')
    await asyncio.sleep(5)  # Simulate network delay
    return f'Downloaded content from {url}'


async def send_whatsapp_message(ctx, to: str, content: str):
    logger = ctx['logger']
    whatsapp_service: WhatsAppService = ctx['whatsapp_service']
    await whatsapp_service.send_message(to, content)
    logger.info(f'Sent WhatsApp message to {to}')
    return f'Sent WhatsApp message to {to}'


async def startup(ctx):
    logger = get_application_logger()
    ctx['session'] = AsyncClient()
    ctx['whatsapp_service'] = WhatsAppService()
    ctx['logger'] = logger
    logger.info("Worker startup complete.")


async def shutdown(ctx):
    await ctx['session'].aclose()
    logger = ctx['logger']
    logger.info("Worker shutdown complete.")

# WorkerSettings defines the settings to use when creating the work,
# It's used by the arq CLI.
# redis_settings might be omitted here if using the default settings
# For a list of all available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker


class WorkerSettings:
    functions = [download_content, send_whatsapp_message]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS
