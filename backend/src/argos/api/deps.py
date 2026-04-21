from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from argos.config import settings

_arq_pool: ArqRedis | None = None


async def init_arq_pool() -> None:
    global _arq_pool
    _arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))


async def close_arq_pool() -> None:
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.aclose()
        _arq_pool = None


async def get_arq_pool() -> ArqRedis:
    assert _arq_pool is not None, "ARQ pool not initialized"
    return _arq_pool
