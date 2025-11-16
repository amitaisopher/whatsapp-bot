"""Job status and types for worker tasks."""
from enum import StrEnum


class JobStatus(StrEnum):
    """Job processing status."""
    
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"
