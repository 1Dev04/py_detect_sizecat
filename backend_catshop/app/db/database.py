import asyncpg
import os
from typing import Optional

_pool: Optional[asyncpg.Pool] = None


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://catuser:catpassword@localhost:5432/catdb"
    )


async def create_db_pool() -> asyncpg.Pool:
    global _pool

    if _pool is not None:
        return _pool

    database_url = get_database_url()

    try:
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        print("✅ Database pool created")
    except Exception as e:
        print("❌ Database connection failed")
        print(f"➡️ DATABASE_URL = {database_url}")
        raise e

    return _pool


async def get_db_pool() -> asyncpg.Pool:
    if _pool is None:
        await create_db_pool()
    return _pool


async def close_db_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        print("🧹 Database pool closed")
