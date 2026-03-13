"""
utils/redis_client.py — Redis connection utility for APDP.

Used by:
    - Agent_Graph/analyser_graph.py  → LangGraph checkpointer (pause/resume HITL)
    - Future: query caching layer
"""

import os
from langgraph.checkpoint.redis import RedisSaver
from config.settings import Settings

settings = Settings()

def get_redis_url() -> str:
    """
    Reads REDIS_URL from .env.
    Expected format: redis://:password@host:port/db
    Example:         redis://:redis_secret@redis:6379/0  (Docker)
                     redis://:redis_secret@localhost:6379/0  (local)
    """
    url = settings.REDIS_URL
    if not url:
        raise ValueError(
            "REDIS_URL not found in environment / .env file.\n"
            "Add it to your .env: REDIS_URL=redis://:redis_secret@redis:6379/0"
        )
    return url


def get_checkpointer() -> RedisSaver:
    """
    Returns a Redis-backed LangGraph checkpointer instance.
    Uses the context manager correctly to get the RedisSaver object.
    """
    with RedisSaver.from_conn_string(get_redis_url()) as checkpointer:
        checkpointer.setup()
        return checkpointer