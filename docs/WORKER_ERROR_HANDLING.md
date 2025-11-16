# ARQ Worker Error Handling Guide

This guide explains how error handling, retries, and dead letter queues work in the WhatsApp chatbot's ARQ workers.

## Overview

The worker system implements a comprehensive error handling strategy with:
- **Automatic retries** with exponential backoff
- **Detailed logging** of all failures
- **Dead Letter Queue (DLQ)** for permanently failed jobs
- **Job deduplication** to prevent duplicate processing

## Retry Strategy

### Retry Configuration

```python
class WorkerSettings:
    max_tries = 3              # Maximum retry attempts
    retry_jobs = True          # Enable automatic retries
    job_timeout = 300          # 5 minutes per job
    keep_result = 3600         # Keep results for 1 hour
    max_jobs = 10              # Maximum concurrent jobs
```

### Exponential Backoff

Jobs are retried with increasing delays:
- **Attempt 1**: Immediate
- **Attempt 2**: 30 seconds delay
- **Attempt 3**: 60 seconds delay
- **Attempt 4**: 120 seconds delay (if max_tries > 3)

**Formula**: `delay = min(30 * 2^(attempt-1), 600)` (capped at 10 minutes)

### How Retries Work

When a job fails, ARQ uses the `Retry` exception:

```python
from arq import Retry
from datetime import timedelta

try:
    # Process job
    result = await process_message(data)
except Exception as e:
    if attempt < max_tries:
        retry_delay = await get_retry_delay(attempt)
        raise Retry(defer=timedelta(seconds=retry_delay))
    else:
        # Move to dead letter queue
        await move_to_dead_letter_queue(ctx, job_key, e)
        raise
```

## Logging

### Log Levels

- **INFO**: Successful processing, retry attempts
- **WARNING**: Transient failures that will be retried
- **ERROR**: Permanent failures, DLQ entries

### Logged Information

Each failure log includes:
```json
{
    "job_key": "whatsapp:123456789",
    "error_type": "ConnectionError",
    "error_message": "Connection timeout",
    "attempt": 2,
    "max_attempts": 3,
    "status": "retry",
    "timestamp": "2025-11-14T10:30:00Z",
    "customer_id": "uuid",
    "from_number": "+1234567890",
    "user_message": "Hello..."
}
```

### Example Log Output

```
2025-11-14 10:30:00 | WARNING | Job whatsapp:123 failed (attempt 1/3), will retry
2025-11-14 10:30:30 | WARNING | Job whatsapp:123 failed (attempt 2/3), will retry
2025-11-14 10:31:30 | ERROR   | Job whatsapp:123 failed after 3 attempts, moving to DLQ
```

## Dead Letter Queue (DLQ)

### Purpose

The DLQ stores jobs that failed after all retry attempts for:
- Manual review and investigation
- Potential manual reprocessing
- Error pattern analysis
- Compliance and auditing

### DLQ Structure

Jobs are stored in Redis with two data structures:

1. **List**: `dead_letter_queue` - Ordered list of failed job keys
2. **Hashes**: `dlq:{job_key}` - Individual job details

### DLQ Entry Format

```json
{
    "job_key": "whatsapp:hash123",
    "error_type": "HTTPError",
    "error_message": "500 Internal Server Error",
    "timestamp": "2025-11-14T10:31:30Z",
    "job_details": {
        "customer_id": "customer-uuid",
        "from_number": "+1234567890",
        "user_message": "Hello, I need help",
        "function": "handle_incoming_whatsapp_message"
    }
}
```

### DLQ Retention

- Jobs remain in DLQ for **7 days**
- Automatically expired by Redis TTL
- Can be manually cleared before expiry

## Managing the Dead Letter Queue

### Command Line Interface

```bash
# View DLQ statistics
python -m app.workers.dlq_manager stats

# List all jobs in DLQ
python -m app.workers.dlq_manager list

# Get count of jobs
python -m app.workers.dlq_manager count

# View specific job details
python -m app.workers.dlq_manager get <job_key>

# Remove specific job
python -m app.workers.dlq_manager remove <job_key>

# Clear entire DLQ (use with caution!)
python -m app.workers.dlq_manager clear
```

### Python API

```python
from app.workers.dlq_manager import DLQManager

# Create manager instance
manager = DLQManager()

# Get statistics
stats = await manager.get_dlq_stats()
print(f"Total failed jobs: {stats['total_jobs']}")

# List jobs
jobs = await manager.list_dlq_jobs(limit=10)

# Get specific job
job = await manager.get_job_details("whatsapp:123")

# Remove from DLQ
removed = await manager.remove_from_dlq("whatsapp:123")

# Clear all
count = await manager.clear_dlq()
```

## Error Handling Patterns

### Pattern 1: Transient Errors (Retry)

For temporary issues like network timeouts:

```python
try:
    response = await api_call()
except (ConnectionError, TimeoutError) as e:
    # These errors should be retried
    raise Retry(defer=timedelta(seconds=retry_delay))
```

### Pattern 2: Permanent Errors (Fail Fast)

For errors that won't succeed on retry:

```python
try:
    validate_input(data)
except ValidationError as e:
    # Don't retry validation errors
    logger.error(f"Invalid input: {e}")
    await move_to_dead_letter_queue(ctx, job_key, e)
    return {"status": "invalid", "error": str(e)}
```

### Pattern 3: Partial Success

For jobs that partially succeed:

```python
try:
    result = await process_message()
    await send_response(result)
    await mark_job_as_processed(ctx, job_key)
except SendError as e:
    # Message processed but sending failed
    logger.warning("Response not sent, marking as processed anyway")
    await mark_job_as_processed(ctx, job_key)
    return {"status": "partial", "error": str(e)}
```

## Best Practices

### 1. Job Idempotency

Always design jobs to be idempotent:

```python
# Check if already processed before starting
if await is_job_already_processed(ctx, job_key):
    return {"status": "already_processed"}

# ... do work ...

# Mark as processed only on success
await mark_job_as_processed(ctx, job_key)
```

### 2. Error Context

Include context in error logs:

```python
await log_job_failure(
    ctx,
    job_key,
    error,
    attempt,
    max_attempts,
    customer_id=customer_id,  # Include relevant context
    from_number=from_number,
    message_type=message_type,
)
```

### 3. Graceful Degradation

Don't let one failure break the entire system:

```python
try:
    await primary_action()
except PrimaryError:
    logger.warning("Primary action failed, trying fallback")
    await fallback_action()
```

### 4. Monitor DLQ

Set up alerts for DLQ growth:

```python
# Check DLQ size regularly
dlq_count = await manager.get_dlq_count()
if dlq_count > 100:
    send_alert("DLQ has grown to", dlq_count, "jobs")
```

### 5. Timeout Handling

Set appropriate timeouts:

```python
class WorkerSettings:
    job_timeout = 300  # 5 minutes
    
# In your code
session = AsyncClient(timeout=40)  # Shorter than job_timeout
```

## Monitoring & Alerts

### Metrics to Track

1. **Job Success Rate**: Successful jobs / Total jobs
2. **Retry Rate**: Jobs retried / Total jobs
3. **DLQ Growth**: New DLQ entries per hour
4. **Processing Time**: Average job duration
5. **Error Types**: Distribution of error types

### Example Monitoring Setup

```python
# In your worker or separate monitoring service
async def monitor_workers():
    manager = DLQManager()
    
    while True:
        stats = await manager.get_dlq_stats()
        
        # Send metrics to monitoring service
        metrics.gauge("dlq.total_jobs", stats["total_jobs"])
        
        for func, count in stats["by_function"].items():
            metrics.gauge(f"dlq.by_function.{func}", count)
        
        await asyncio.sleep(60)  # Check every minute
```

### Alert Rules

- DLQ size > 50: Warning
- DLQ size > 100: Critical
- Same error type > 10 times: Investigation needed
- Jobs in DLQ > 24 hours: Manual review required

## Troubleshooting

### High Retry Rate

**Symptoms**: Many jobs being retried

**Possible Causes**:
- External service having issues
- Network connectivity problems
- Rate limiting

**Solutions**:
- Check external service status
- Increase retry delays
- Implement circuit breaker pattern

### Jobs Stuck in DLQ

**Symptoms**: DLQ growing continuously

**Possible Causes**:
- Systematic error in code
- Invalid data in database
- External service permanently down

**Solutions**:
1. Check DLQ stats for patterns
2. Review error messages
3. Fix underlying issue
4. Clear DLQ after fix

### Jobs Taking Too Long

**Symptoms**: Job timeouts

**Possible Causes**:
- Database queries too slow
- External API slow
- Processing too much data

**Solutions**:
- Optimize database queries
- Increase timeout if appropriate
- Break large jobs into smaller chunks

## Testing Error Handling

### Unit Tests

```python
@pytest.mark.asyncio
async def test_job_retry_on_failure():
    ctx = {"logger": Mock(), "redis": AsyncMock()}
    
    # Simulate failure on first attempt
    with patch("app.services.api.call") as mock_call:
        mock_call.side_effect = [ConnectionError(), "success"]
        
        # First call should raise Retry
        with pytest.raises(Retry):
            await process_job(ctx, "data")
        
        # Second call should succeed
        result = await process_job(ctx, "data")
        assert result == "success"
```

### Integration Tests

```bash
# Test with real Redis
ENVIRONMENT=development pytest tests/test_workers.py -v

# Test DLQ management
python -m app.workers.dlq_manager stats
```

## Summary

The error handling system provides:
- ✅ Automatic retries with exponential backoff
- ✅ Comprehensive logging of all failures
- ✅ Dead letter queue for manual review
- ✅ Job deduplication to prevent duplicates
- ✅ Graceful degradation on failures
- ✅ Monitoring and alerting capabilities

This ensures your WhatsApp chatbot is resilient and failures are properly tracked and handled.

## Examples

### Viewing Failed Jobs

```bash
$ python -m app.workers.dlq_manager list

1. Job: whatsapp:9876543210
   Error: ConnectionError - Connection timeout
   Time: 2025-11-14T10:31:30Z

2. Job: send:1234567890
   Error: HTTPError - 500 Internal Server Error
   Time: 2025-11-14T10:35:15Z
```

### Getting Statistics

```bash
$ python -m app.workers.dlq_manager stats

Dead Letter Queue Statistics
Total jobs: 23

By function:
  handle_incoming_whatsapp_message: 15
  send_whatsapp_message: 6
  download_content: 2

By error type:
  ConnectionError: 10
  HTTPError: 8
  TimeoutError: 5
```

### Clearing the Queue

```bash
$ python -m app.workers.dlq_manager clear
Cleared 23 jobs from DLQ
```

## Integration with Existing Code

The error handling is now fully integrated into your worker tasks:

1. **`download_content`** - Retries with exponential backoff, logs failures, moves to DLQ after 3 attempts
2. **`handle_incoming_whatsapp_message`** - Same retry logic, returns graceful error status instead of failing
3. **`send_whatsapp_message`** - Retries on failure, comprehensive logging

All jobs automatically benefit from:
- Job deduplication (no duplicate processing)
- Detailed failure logging
- Dead letter queue storage
- Exponential backoff retries
