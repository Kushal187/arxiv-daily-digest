from __future__ import annotations

import hashlib
import logging
from contextlib import contextmanager

from .config import settings

logger = logging.getLogger(__name__)

_pool = None


def advisory_lock_key(name: str) -> int:
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return int(digest[:15], 16)


def _get_pool():
    global _pool
    if _pool is not None:
        return _pool

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for the worker")

    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    _pool = ConnectionPool(
        conninfo=settings.database_url,
        min_size=2,
        max_size=10,
        kwargs={"row_factory": dict_row},
    )
    logger.info("Database connection pool created (min=2, max=10)")
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


@contextmanager
def get_connection():
    pool = _get_pool()
    with pool.connection() as connection:
        yield connection
