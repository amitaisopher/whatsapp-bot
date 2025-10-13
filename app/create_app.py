from logging import Logger
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import sentry_sdk

from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.whatsapp import router as whatsapp_router
from app.core.logging import setup_sentry_logging, InterceptHandler
from app.core.config import settings
from app.core.logging import verify_sentry_configuration


def create_app() -> FastAPI:
    """Create and configure a FastAPI application."""

    # Initialize Sentry logging prior to app creation
    # This ensures that any errors during app creation are captured by Sentry
    # and that the logging configuration is set up correctly.
    # This is particularly useful for capturing errors in the app startup phase.
    setup_sentry_logging()

    
    app = FastAPI(title=settings.app_name)

    uvicorn_logger: Logger = logging.getLogger("app")

    # Removing uvicorn default logger
    for name in logging.root.manager.loggerDict:
        if name in ("uvicorn.error", "uvicorn.access", "fastaspi"):
            uvicorn_logger = logging.getLogger(name)
            uvicorn_logger.handlers.clear()
            uvicorn_logger.setLevel(level=logging.INFO)
            uvicorn_logger.addHandler(hdlr=InterceptHandler())

    # Add global exception handlers
    # Global exception handler for unhandled exceptions

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Add request context to Sentry if enabled
        if verify_sentry_configuration():
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("handler", "global_exception_handler")
                scope.set_context("request", {
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers),
                })
            # Capture the exception in Sentry before handling it
            sentry_sdk.capture_exception(exc)

        uvicorn_logger.error(
            f"Unhandled exception occurred: {type(exc).__name__}: {str(exc)}\n"
            f"Request URL: {request.url}\n"
            f"Request method: {request.method}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "status_code": 500,
            },
        )

    # Exception handler for HTTP exceptions
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Capture HTTP exceptions with status code 500 or higher in Sentry if enabled
        if exc.status_code >= 500 and verify_sentry_configuration():
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("handler", "http_exception_handler")
                scope.set_context("request", {
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers),
                })
            sentry_sdk.capture_exception(exc)

        uvicorn_logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}\n"
            f"Request URL: {request.url}\n"
            f"Request method: {request.method}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
            },
        )

    # Exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        uvicorn_logger.warning(
            f"Validation error: {str(exc)}\n"
            f"Request URL: {request.url}\n"
            f"Request method: {request.method}"
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "status_code": 422,
            },
        )

    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(whatsapp_router, prefix="/api/v1", tags=["WhatsApp"])

    return app
