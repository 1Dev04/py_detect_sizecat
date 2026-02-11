from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.callback_flutter import router as callback_router
from app.api.search_flutter import router as search_router
from app.api.vision import router as vision_router
from app.auth.login import router as login_router
from app.auth.register import router as sign_up_router
from app.db.database import create_db_pool, close_db_pool
from app.core.firebase import init_firebase


@asynccontextmanager
async def lifespan(app: FastAPI):

    # --- DB ---
    try:
        await create_db_pool()
    except Exception as e:
        print(f"⚠️ Database not ready, continue without DB: {e}")

    # --- Firebase ---
    try:
        init_firebase()
        print("✅ Firebase initialized")
    except Exception as e:
        print(f"⚠️ Firebase skipped: {e}")

    print("🚀 App startup complete")
    yield

    # --- Shutdown ---
    try:
        await close_db_pool()
        print("🧹 Database pool closed")
    except Exception:
        pass

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

app.include_router(callback_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(login_router, prefix="/api")
app.include_router(sign_up_router, prefix="/api")
app.include_router(vision_router, prefix="/api")



@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "catshop-backend"
    }



# CORS - อนุญาตทุก origin (production ควรระบุ domain เฉพาะ)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (สำคัญสำหรับ Render)
@app.get("/")
def read_root():
    return {
        "message": "🐱 Cat Shop Backend API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api"
        }
    }

