"""
mock_api/db.py  –  Async connection pool for Postgres via asyncpg.

Only mock_api touches the database; ai_backend never imports this.
"""

import os
import asyncpg

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Return the module-level connection pool (created lazily)."""
    global _pool
    if _pool is None:
        # DATABASE_URL comes in SQLAlchemy-style; asyncpg needs plain postgres://
        dsn = os.environ.get(
            "DATABASE_URL",
            "postgresql://support_user:support_pass@postgres:5432/support_ai",
        )
        # Normalise driver prefix so asyncpg can parse it
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
        _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
