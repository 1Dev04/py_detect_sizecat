from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    #App
    APP_NAME: str = "ABCat Shop API"
    APP_HOST: Optional[str] = "0.0.0.0"
    APP_PORT: Optional[int] = 8000
    DEBUG: bool = False

    #Database
    DATABASE_URL: str
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    #Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None 
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    #Firebase (not JWT)
    FIREBASE_SERVICE_ACCOUNT_KEY: str = "app/serviceAccountKey.json"

    # #OpenAI
    # OPENAI_API_KEY: str 

   
    #CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://your-app.vercel.app"
    ]

    # Upload Setting
    UPLOAD_DIR: Optional[str] = "uploads"
    MAX_FILE_SIZE: Optional[int] = 10485760  # 10MB

    # ============================================
    # Model Configuration
    # ============================================
    model_config = {
        "env_file": ".env",
        "extra": "ignore" 
    }
    
    # ============================================
    # Property: ใช้ cloudinary_name ถ้า CLOUDINARY_CLOUD_NAME ไม่มี
    # ============================================
    @property
    def get_cloudinary_cloud_name(self) -> str:
        return self.CLOUDINARY_CLOUD_NAME or self.cloudinary_name
    
    @property
    def get_cloudinary_api_key(self) -> str:
        return self.CLOUDINARY_API_KEY or self.cloudinary_api_key
    
    @property
    def get_cloudinary_api_secret(self) -> str:
        return self.CLOUDINARY_API_SECRET or self.cloudinary_api_secret
    
    @property
    def get_database_url(self) -> str:
        """สร้าง DATABASE_URL จาก postgres_* ถ้าไม่มี DATABASE_URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5432/{self.POSTGRES_DB}"
        
        raise ValueError("DATABASE_URL or POSTGRES_* variables required")

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()