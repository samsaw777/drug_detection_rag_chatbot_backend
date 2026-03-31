from psycopg_pool import AsyncConnectionPool # type: ignore
from config.settings import get_settings

Settings = get_settings()

_pool = None

async def get_main_pool() -> AsyncConnectionPool:
    global _pool

    if _pool is not None:
        return _pool

    db_url = Settings.DATABASE_URL

    if not db_url:
        raise ValueError(
            "DATABASE_URL not found in the env file."
        )
    
    _pool = AsyncConnectionPool(
        conninfo = db_url,
        open = False,
        kwargs={"autocommit": True, "prepare_threshold": 0}
    )

    await _pool.open()
    return _pool


async def close_main_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None