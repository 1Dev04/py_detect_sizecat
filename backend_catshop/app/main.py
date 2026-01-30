from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import os
from contextlib import asynccontextmanager

from app.api.callback_flutter import router as home_router 

db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    DATABASE_URL = os.getenv("DATABASE_URL")
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    print("✅ Database connected")
    yield
    await db_pool.close()
    print("❌ Database disconnected")

app = FastAPI(
    title="ABC SHOP API",
    description="API for ABC Shop Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇👇👇 สำคัญมาก
app.include_router(home_router)

# Health
@app.get("/health")
async def health_check():
    async with db_pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Cat Shop API",
        "docs": "/docs",
        "health": "/health"
    }
