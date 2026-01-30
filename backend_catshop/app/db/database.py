import asyncpg
import os
from typing import Optional

# Database connection pool (singleton)
_pool: Optional[asyncpg.Pool] = None


async def create_db_pool() -> asyncpg.Pool:
    """
    Create database connection pool
    """
    global _pool
    
    if _pool is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://catuser:catpassword@postgres:5432/catdb"
        )
        
        try:
            _pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )
            
            print("✅ Database pool created successfully")
        except Exception as e:
            print(f"❌ Failed to create database pool: {e}")
            raise
    
    return _pool


async def close_db_pool():
    """
    Close database connection pool
    """
    global _pool
    
    if _pool is not None:
        await _pool.close()
        _pool = None
        print("✅ Database pool closed")


async def get_db_pool() -> asyncpg.Pool:
    """
    Dependency for getting database pool
    """
    global _pool
    if _pool is None:
        _pool = await create_db_pool()
    return _pool