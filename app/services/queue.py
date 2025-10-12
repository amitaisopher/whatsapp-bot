from typing import Optional
from arq.jobs import Job
from httpx import AsyncClient
from arq.connections import RedisSettings, ArqRedis
from arq import create_pool
from functools import lru_cache

from app.core.redis import REDIS_SETTINGS



class ArqService:
    def __init__(self, redis_settings: RedisSettings):
        self._settings = redis_settings
        self._pool: Optional[ArqRedis] = None

    @classmethod
    async def create(cls, redis_settings: RedisSettings) -> "ArqService":
        self = cls(redis_settings)
        self._pool = await create_pool(redis_settings)
        return self
    
    # ----- explicit connect/close -----
    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await create_pool(self._settings)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
    
    # ----- Async context manager -----
    async def __aenter__(self) -> "ArqService":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    @property
    def pool(self) -> ArqRedis:
        if self._pool is None:
            raise RuntimeError("ArqService not connected. Call `await connect()` or use the async factory/context manager.")
        return self._pool

    async def enqueue(self, job_name: str, *args, **kwargs) -> Job | None:
        return await self.pool.enqueue_job(job_name, *args, **kwargs)


@lru_cache
def get_arq_service() -> ArqService:
    return ArqService(REDIS_SETTINGS)

arq_service = get_arq_service()

if __name__ == "__main__":
    import asyncio
    
    async def main():
        async with ArqService(REDIS_SETTINGS) as arq_service:
            job: Job | None = await arq_service.enqueue('download_content', 'https://zubi.com')
            if job:
                print(f'Enqueued job: {job.job_id}')
            else:
                print('Failed to enqueue job')
    asyncio.run(main())