# Workers Module

This module contains the ARQ worker implementation for asynchronous job processing.

## Structure

The workers module is organized into focused modules for better maintainability:

### `job_status.py`
Defines job status enum used throughout the worker system.

**Exports:**
- `JobStatus` - Enum for job processing states (PROCESSING, SUCCESS, FAILED, RETRY, DEAD_LETTER)

### `job_deduplication.py`
Redis-based job deduplication to prevent duplicate processing of the same job.

**Key Functions:**
- `is_job_already_processed(ctx, job_key)` - Check if a job was already processed
- `mark_job_as_processed(ctx, job_key, ttl)` - Mark a job as successfully completed

### `error_handling.py`
Comprehensive error handling, retry logic, and dead letter queue management.

**Key Functions:**
- `log_job_failure(ctx, job_key, error, attempt, max_attempts, **job_details)` - Log detailed failure information
- `move_to_dead_letter_queue(ctx, job_key, error, **job_details)` - Move failed jobs to DLQ
- `get_retry_delay(attempt)` - Calculate exponential backoff delay (30s, 60s, 120s, capped at 600s)

### `task_functions.py`
Actual task implementations that process jobs.

**Task Functions:**
- `download_content(ctx, url)` - Download content from URL
- `handle_incoming_whatsapp_message(ctx, customer_id, from_number, user_message, message_id)` - Process incoming WhatsApp messages
- `send_whatsapp_message(ctx, to, content, message_id)` - Send WhatsApp messages

All task functions include:
- Job deduplication
- Automatic retry with exponential backoff
- Dead letter queue integration
- Comprehensive logging

### `lifecycle.py`
Worker lifecycle management (startup and shutdown).

**Key Functions:**
- `startup(ctx)` - Initialize worker context with services and connections
- `shutdown(ctx)` - Clean up resources on worker shutdown

### `tasks.py`
Main worker configuration that ties everything together.

**Exports:**
- `WorkerSettings` - ARQ worker configuration class

### `dlq_manager.py`
Command-line tool and API for managing the dead letter queue.

**Features:**
- List failed jobs
- View job details
- Remove jobs from DLQ
- Clear entire DLQ
- View statistics

## Usage

### Starting the Worker

```bash
# Using arq CLI
arq app.workers.tasks.WorkerSettings

# Using Docker
docker-compose up worker
```

### Managing Dead Letter Queue

```bash
# Count jobs in DLQ
python -m app.workers.dlq_manager count

# List jobs
python -m app.workers.dlq_manager list

# View stats
python -m app.workers.dlq_manager stats

# Get job details
python -m app.workers.dlq_manager get <job_key>

# Remove a job
python -m app.workers.dlq_manager remove <job_key>

# Clear all jobs
python -m app.workers.dlq_manager clear
```

## Adding New Tasks

To add a new task function:

1. Create your task function in `task_functions.py`:

```python
async def my_new_task(ctx: dict[str, Any], param1: str, param2: int) -> str:
    """
    Description of what the task does.
    
    Args:
        ctx: Worker context
        param1: Description
        param2: Description
    
    Returns:
        Result description
        
    Raises:
        Retry: To retry the job after a delay
    """
    logger = ctx["logger"]
    job_info = ctx.get("job_try", 1)
    max_tries = 3

    # Create unique job key
    job_key = f"my_task:{hash((param1, param2))}"

    # Check if already processed
    if await is_job_already_processed(ctx, job_key):
        logger.info(f"Job {job_key} already processed, skipping")
        return f"Already processed {param1}"

    try:
        logger.info(f"Processing {job_key} (attempt {job_info})")
        
        # Your task logic here
        result = do_something(param1, param2)
        
        # Mark as processed on success
        await mark_job_as_processed(ctx, job_key)
        logger.info(f"Successfully completed job {job_key}")
        return result

    except Exception as e:
        # Log the failure
        await log_job_failure(
            ctx,
            job_key,
            e,
            job_info,
            max_tries,
            param1=param1,
            param2=param2,
            function="my_new_task",
        )
        
        if job_info < max_tries:
            # Calculate retry delay and retry
            retry_delay = await get_retry_delay(job_info)
            logger.info(f"Retrying job {job_key} after {retry_delay}s")
            raise Retry(defer=timedelta(seconds=retry_delay))
        else:
            # Move to dead letter queue
            await move_to_dead_letter_queue(
                ctx,
                job_key,
                e,
                param1=param1,
                param2=param2,
                function="my_new_task",
            )
            raise
```

2. Register the task in `tasks.py`:

```python
from app.workers.task_functions import (
    download_content,
    handle_incoming_whatsapp_message,
    send_whatsapp_message,
    my_new_task,  # Add your task
)

class WorkerSettings:
    functions = [
        download_content,
        send_whatsapp_message,
        handle_incoming_whatsapp_message,
        my_new_task,  # Add your task
    ]
    # ... rest of configuration
```

## Error Handling

The worker implements comprehensive error handling:

1. **Retry Logic**: Failed jobs are automatically retried up to 3 times with exponential backoff
2. **Dead Letter Queue**: Jobs that fail after max retries are moved to DLQ for manual review
3. **Job Deduplication**: Prevents duplicate processing of the same job
4. **Graceful Degradation**: Some tasks return error status instead of failing hard

## Configuration

Worker settings can be adjusted in `tasks.py`:

- `max_tries`: Maximum retry attempts (default: 3)
- `retry_jobs`: Enable/disable retries (default: True)
- `job_timeout`: Job timeout in seconds (default: 300)
- `keep_result`: How long to keep results (default: 3600)
- `max_jobs`: Maximum concurrent jobs (default: 10)

## Testing

Tests are organized by functionality:

- `test_worker_error_handling.py` - Error handling, retry logic, and DLQ tests
- `test_tasks_deduplication.py` - Job deduplication tests
- `test_whatsapp_service.py` - WhatsApp service tests

Run all worker tests:

```bash
pytest tests/test_worker*.py -v
pytest tests/test_tasks*.py -v
```
