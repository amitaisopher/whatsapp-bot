from fastapi import FastAPI
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.whatsapp import router as whatsapp_router
from app.core.logging import setup_logging
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure a FastAPI application."""
    
    setup_logging()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(whatsapp_router, prefix="/api/v1", tags=["WhatsApp"])

    return app
