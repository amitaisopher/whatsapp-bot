"""
ARQ Worker Tasks Configuration.

This module defines the worker tasks and configuration for the ARQ worker.
Task implementations are separated into focused modules for better maintainability.

Module structure:
- job_status.py: Job status enum
- job_deduplication.py: Job deduplication logic using Redis
- error_handling.py: Error handling, retry logic, and dead letter queue
- task_functions.py: Actual task implementations
- lifecycle.py: Worker startup and shutdown
"""
from app.core.redis import REDIS_SETTINGS
from app.workers.lifecycle import startup, shutdown
from app.workers.task_functions import (
    download_content,
    handle_incoming_whatsapp_message,
    send_whatsapp_message,
)


# WorkerSettings defines the settings to use when creating the worker.
# It's used by the arq CLI.
# For a list of all available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker

class WorkerSettings:
    """
    ARQ Worker configuration.
    
    Defines the tasks to be executed, lifecycle hooks, and worker behavior.
    For all available settings, see: https://arq-docs.helpmanual.io/#arq.worker.Worker
    """
    
    # Task functions to be registered with the worker
    functions = [
        download_content,
        send_whatsapp_message,
        handle_incoming_whatsapp_message,
    ]
    
    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown
    
    # Redis connection settings
    redis_settings = REDIS_SETTINGS

    # Job retry and processing configuration
    max_tries = 3  # Maximum retry attempts
    retry_jobs = True  # Enable job retries
    job_timeout = 300  # Job timeout in seconds (5 minutes)
    keep_result = 3600  # Keep job results for 1 hour

    # Concurrency control
    max_jobs = 10  # Maximum concurrent jobs per worker
