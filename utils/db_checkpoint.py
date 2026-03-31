from psycopg_pool import AsyncConnectionPool # type: ignore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver # type: ignore
from config.settings import get_settings

settings = get_settings()

_pool = None
_checkpointer = None


async def get_checkpointer() -> AsyncPostgresSaver:
    global _pool, _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    db_url = settings.DATABASE_URL_CHECKPOINT
    if not db_url:
        raise ValueError(
            "DATABASE_URL not found in environment / .env file.\n"
            "Add it to your .env: DATABASE_URL=postgresql://user:pass@host:port/db"
        )

    _pool = AsyncConnectionPool(
        conninfo=db_url,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    await _pool.open()

    _checkpointer = AsyncPostgresSaver(conn=_pool)
    await _checkpointer.setup()
    return _checkpointer