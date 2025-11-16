"""
Dead Letter Queue Manager for ARQ Workers.

This module provides utilities to manage failed jobs in the dead letter queue.
"""
import asyncio
from typing import List, Dict, Any, Optional

import redis.asyncio as redis
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class DLQManager:
    """Manager for dead letter queue operations."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.from_url(
                url=settings.redis_url,
                decode_responses=True,
            )
            logger.info("Connected to Redis for DLQ management")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.aclose()
            logger.info("Disconnected from Redis")
    
    async def get_dlq_count(self) -> int:
        """Get the number of jobs in the dead letter queue."""
        await self.connect()
        count = await self.redis.llen("dead_letter_queue")
        return count
    
    async def list_dlq_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List jobs in the dead letter queue.
        
        Args:
            limit: Maximum number of jobs to retrieve
        
        Returns:
            List of job details
        """
        await self.connect()
        
        # Get job keys from the queue
        job_keys = await self.redis.lrange("dead_letter_queue", 0, limit - 1)
        
        jobs = []
        for job_key in job_keys:
            job_data = await self.redis.hgetall(f"dlq:{job_key}")
            if job_data:
                jobs.append(job_data)
        
        return jobs
    
    async def get_job_details(self, job_key: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific job in the DLQ.
        
        Args:
            job_key: Unique job identifier
        
        Returns:
            Job details or None if not found
        """
        await self.connect()
        job_data = await self.redis.hgetall(f"dlq:{job_key}")
        return job_data if job_data else None
    
    async def remove_from_dlq(self, job_key: str) -> bool:
        """
        Remove a job from the dead letter queue.
        
        Args:
            job_key: Unique job identifier
        
        Returns:
            True if removed, False otherwise
        """
        await self.connect()
        
        # Remove from list
        removed = await self.redis.lrem("dead_letter_queue", 0, job_key)
        
        # Delete the job data
        await self.redis.delete(f"dlq:{job_key}")
        
        if removed:
            logger.info(f"Removed job {job_key} from DLQ")
        
        return removed > 0
    
    async def clear_dlq(self) -> int:
        """
        Clear all jobs from the dead letter queue.
        
        Returns:
            Number of jobs cleared
        """
        await self.connect()
        
        # Get all job keys
        job_keys = await self.redis.lrange("dead_letter_queue", 0, -1)
        
        # Delete all job data
        pipeline = self.redis.pipeline()
        for job_key in job_keys:
            pipeline.delete(f"dlq:{job_key}")
        
        # Delete the queue list
        pipeline.delete("dead_letter_queue")
        
        await pipeline.execute()
        
        count = len(job_keys)
        logger.info(f"Cleared {count} jobs from DLQ")
        
        return count
    
    async def requeue_job(self, job_key: str) -> bool:
        """
        Move a job from DLQ back to the main queue for reprocessing.
        
        Args:
            job_key: Unique job identifier
        
        Returns:
            True if requeued, False otherwise
        """
        await self.connect()
        
        job_data = await self.get_job_details(job_key)
        if not job_data:
            logger.warning(f"Job {job_key} not found in DLQ")
            return False
        
        # TODO: Implement requeuing logic based on function name
        # This would require calling the appropriate ARQ enqueue function
        # with the original job parameters
        
        logger.info(f"Requeuing job {job_key} - implementation needed")
        return False
    
    async def get_dlq_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the dead letter queue.
        
        Returns:
            Dictionary with DLQ statistics
        """
        await self.connect()
        
        total_count = await self.get_dlq_count()
        jobs = await self.list_dlq_jobs(limit=1000)
        
        # Aggregate statistics
        function_counts = {}
        error_type_counts = {}
        
        for job in jobs:
            # Parse job_details if it's a string representation
            job_details_str = job.get("job_details", "{}")
            
            # Try to extract function name from job_details
            if "function" in job_details_str:
                # Simple parsing - you may want to improve this
                func = "unknown"
                try:
                    import ast
                    job_details_dict = ast.literal_eval(job_details_str)
                    func = job_details_dict.get("function", "unknown")
                except:
                    func = "unknown"
            else:
                func = "unknown"
            
            error_type = job.get("error_type", "unknown")
            
            function_counts[func] = function_counts.get(func, 0) + 1
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            "total_jobs": total_count,
            "by_function": function_counts,
            "by_error_type": error_type_counts,
            "sample_jobs": jobs[:10],  # First 10 jobs
        }


async def main():
    """CLI for managing dead letter queue."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.workers.dlq_manager <command>")
        print("Commands:")
        print("  list           - List jobs in DLQ")
        print("  count          - Get DLQ count")
        print("  stats          - Get DLQ statistics")
        print("  clear          - Clear all jobs from DLQ")
        print("  remove <key>   - Remove specific job from DLQ")
        print("  get <key>      - Get details of specific job")
        return
    
    command = sys.argv[1]
    manager = DLQManager()
    
    try:
        if command == "list":
            jobs = await manager.list_dlq_jobs()
            if not jobs:
                print("No jobs in DLQ")
            else:
                for i, job in enumerate(jobs, 1):
                    print(f"\n{i}. Job: {job.get('job_key')}")
                    print(f"   Error: {job.get('error_type')} - {job.get('error_message')}")
                    print(f"   Time: {job.get('timestamp')}")
        
        elif command == "count":
            count = await manager.get_dlq_count()
            print(f"Jobs in DLQ: {count}")
        
        elif command == "stats":
            stats = await manager.get_dlq_stats()
            print(f"\nDead Letter Queue Statistics")
            print(f"Total jobs: {stats['total_jobs']}")
            print(f"\nBy function:")
            for func, count in stats['by_function'].items():
                print(f"  {func}: {count}")
            print(f"\nBy error type:")
            for error_type, count in stats['by_error_type'].items():
                print(f"  {error_type}: {count}")
        
        elif command == "clear":
            count = await manager.clear_dlq()
            print(f"Cleared {count} jobs from DLQ")
        
        elif command == "remove" and len(sys.argv) > 2:
            job_key = sys.argv[2]
            removed = await manager.remove_from_dlq(job_key)
            if removed:
                print(f"Removed job {job_key} from DLQ")
            else:
                print(f"Job {job_key} not found in DLQ")
        
        elif command == "get" and len(sys.argv) > 2:
            job_key = sys.argv[2]
            job = await manager.get_job_details(job_key)
            if job:
                print(f"\nJob Details for {job_key}:")
                for key, value in job.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Job {job_key} not found in DLQ")
        
        else:
            print(f"Unknown command: {command}")
    
    finally:
        await manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
