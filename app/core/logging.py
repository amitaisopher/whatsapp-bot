import sys
from functools import lru_cache
import logging
from loguru import logger
import loguru
from app.core.config import settings
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from enum import StrEnum


class LogLevels(StrEnum):
    """Enum for log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def verify_sentry_configuration() -> bool:
    """
    Check if required environment variables for integration with Sentry exist.
    """
    return settings.sentry_enabled and bool(settings.sentry_dsn)


def setup_sentry_logging() -> None:
    """
    Setup logging configuration for the application.
    """
    sentry_logger = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events to Sentry
    )

    # Configure Sentry for error tracking
    if verify_sentry_configuration():
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration(), sentry_logger],
            traces_sample_rate=1.0,  # Adjust this value for performance monitoring
            # Add data like request headers and IP for users,
            # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
            send_default_pii=True,
        )
        logger.info("Sentry logging initialized")
    else:
        logger.info("Sentry logging disabled")


class InterceptHandler(logging.Handler):
    """
    Custom logging handler to intercept log messages and redirect them to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level: str = logger.level(record.levelname).name
        except ValueError:
            level: int = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """
    Set up logging for use throughout the application.
    """
    logger.remove()
    # Set log level from settings
    log_level = settings.log_level.upper()
    if log_level not in LogLevels.__members__:
        log_level = LogLevels.INFO.value
    # Optionally log to file
    if settings.log_to_file:
        logger.add(
            settings.log_file_path,
            level=log_level,
            rotation="10 MB",  # Rotate after 10 MB
            retention="10 days",  # Keep logs for 10 days
            compression="zip",  # Compress rotated logs
        )
    
    logger.add(
        sys.stdout,
        level="INFO",
        colorize=True,
    )


@lru_cache()
def get_application_logger() -> "loguru.Logger":
    """
    Get a loguru logger instance for the application.
    """
    setup_logging()
    return logger
