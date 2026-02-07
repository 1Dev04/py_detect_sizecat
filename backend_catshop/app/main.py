from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.callback_flutter import router as callback_router
from app.api.search_flutter import router as search_router
from app.api.vision import router as vision_router
from app.auth.login import router as login_router
from app.auth.register import router as sign_up_router
from app.db.database import create_db_pool, close_db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_pool()
    print("🚀 App startup complete")
    yield
    await close_db_pool()
    print("🧹 App shutdown complete")

app = FastAPI(
    title="ABC SHOP API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(callback_router)
app.include_router(search_router)
app.include_router(login_router)
app.include_router(sign_up_router)
app.include_router(vision_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Cat Shop API is running"}