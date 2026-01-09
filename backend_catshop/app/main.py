# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.api.cat import router as cat_router
from app.services.detectSizeCat import DetectionService

load_dotenv()

app = FastAPI(
    title="Cat Detection API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting API...")
    DetectionService.initialize_model()

app.include_router(cat_router, prefix="/api", tags=["Cat"])

@app.get("/")
def root():
    return {"status": "ok"}
