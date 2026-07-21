"""
mock_api/db.py  –  Async connection pool for Postgres via asyncpg.

Only mock_api touches the database; ai_backend never imports this.
"""

import os
import asyncpg

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool | None:
    """Return the module-level connection pool (created lazily). Returns None if database is unreachable."""
    global _pool
    if _pool is None:
        dsn = os.environ.get(
            "DATABASE_URL",
            "postgresql://support_user:support_pass@localhost:5432/support_ai",
        )
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
        try:
            _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5, timeout=2.0)
        except Exception:
            _pool = None
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
        except Exception:
            pass
        _pool = None
