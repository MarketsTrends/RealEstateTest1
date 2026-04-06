from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg


def can_connect(database_url: str | None) -> bool:
    if not database_url:
        return False
    try:
        with psycopg.connect(database_url):
            return True
    except Exception:
        return False


@contextmanager
def get_connection(database_url: str) -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(database_url)
    try:
        yield conn
    finally:
        conn.close()
