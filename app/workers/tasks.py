# tasks.py
from httpx import AsyncClient

from app.core.redis import REDIS_SETTINGS
from app.services.whatsapp import WhatsAppService


async def download_content(ctx, url):
    session: AsyncClient = ctx['session']
    # response = await session.get(url)
    # print(f'{url}: {response.text:.80}...')
    # return len(response.text)
    print(f'Allegedly downloaded content from {url}')
    return f'Downloaded content from {url}'

async def send_whatsapp_message(ctx, to: str, content: str):
    whatsapp_service: WhatsAppService = ctx['whatsapp_service']
    await whatsapp_service.send_message(to, content)
    return f'Sent WhatsApp message to {to}'

async def startup(ctx):
    ctx['session'] = AsyncClient()
    ctx['whatsapp_service'] = WhatsAppService()

async def shutdown(ctx):
    await ctx['session'].aclose()

# WorkerSettings defines the settings to use when creating the work,
# It's used by the arq CLI.
# redis_settings might be omitted here if using the default settings
# For a list of all available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content, send_whatsapp_message]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS