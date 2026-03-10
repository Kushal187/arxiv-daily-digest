from __future__ import annotations

import hashlib
from contextlib import contextmanager

from .config import settings


def advisory_lock_key(name: str) -> int:
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return int(digest[:15], 16)


@contextmanager
def get_connection():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for the worker")

    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(settings.database_url, row_factory=dict_row) as connection:
        yield connection
