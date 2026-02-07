from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

# ============================================
# Schema สำหรับสร้างแมว (Create)
# ============================================
class CatCreate(BaseModel):
    """Schema for creating a new cat"""
    
    name: str = Field(..., description="Cat name or color (e.g., Orange_Cat)")
    breed: Optional[str] = Field(None, description="Cat breed (e.g., Persian)")
    age: Optional[int] = Field(None, ge=0, le=30, description="Cat age in years")
    weight: float = Field(..., gt=0, description="Cat weight in kg")
    
    size_category: str = Field(..., description="Size category: XS, S, M, L, XL")
    chest_cm: float = Field(..., gt=0, description="Chest circumference in cm")
    neck_cm: Optional[float] = Field(None, gt=0, description="Neck circumference in cm")
    body_length_cm: Optional[float] = Field(None, gt=0, description="Body length in cm")
    
    confidence: float = Field(..., ge=0, le=1, description="AI prediction confidence (0-1)")
    image_url: str = Field(..., description="Full image URL from Cloudinary")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    
    @validator('size_category')
    def validate_size(cls, v):
        allowed = ['XS', 'S', 'M', 'L', 'XL']
        if v not in allowed:
            raise ValueError(f'Size must be one of {allowed}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Orange_Cat",
                "breed": "Persian",
                "age": 2,
                "weight": 3.5,
                "size_category": "M",
                "chest_cm": 44.6,
                "neck_cm": 25.3,
                "body_length_cm": 38.2,
                "confidence": 0.95,
                "image_url": "https://res.cloudinary.com/xxx/cat.jpg",
                "thumbnail_url": "https://res.cloudinary.com/xxx/cat_thumb.jpg"
            }
        }

# ============================================
# Schema สำหรับอัปเดตแมว (Update)
# ============================================
class CatUpdate(BaseModel):
    """Schema for updating cat data (all fields optional)"""
    
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=30)
    weight: Optional[float] = Field(None, gt=0)
    
    size_category: Optional[str] = None
    chest_cm: Optional[float] = Field(None, gt=0)
    neck_cm: Optional[float] = Field(None, gt=0)
    body_length_cm: Optional[float] = Field(None, gt=0)
    
    confidence: Optional[float] = Field(None, ge=0, le=1)
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    @validator('size_category')
    def validate_size(cls, v):
        if v is not None:
            allowed = ['XS', 'S', 'M', 'L', 'XL']
            if v not in allowed:
                raise ValueError(f'Size must be one of {allowed}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Fluffy",
                "age": 3,
                "weight": 4.2
            }
        }

# ============================================
# Schema สำหรับแสดงผลแมว (Response)
# ============================================
class CatResponse(BaseModel):
    """Schema for cat response"""
    
    id: int
    firebase_uid: str
    
    name: str
    breed: Optional[str]
    age: Optional[int]
    weight: float
    
    size_category: str
    chest_cm: float
    neck_cm: Optional[float]
    body_length_cm: Optional[float]
    
    confidence: float
    image_url: str
    thumbnail_url: Optional[str]
    
    detected_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Pydantic v2
        # orm_mode = True  # Pydantic v1
        json_schema_extra = {
            "example": {
                "id": 1,
                "firebase_uid": "firebase_user_abc123",
                "name": "Orange_Cat",
                "breed": "Persian",
                "age": 2,
                "weight": 3.5,
                "size_category": "M",
                "chest_cm": 44.6,
                "neck_cm": 25.3,
                "body_length_cm": 38.2,
                "confidence": 0.95,
                "image_url": "https://res.cloudinary.com/xxx/cat.jpg",
                "thumbnail_url": "https://res.cloudinary.com/xxx/cat_thumb.jpg",
                "detected_at": "2025-02-04T10:30:00Z",
                "updated_at": "2025-02-04T10:30:00Z"
            }
        }

# ============================================
# Schema สำหรับ List Response
# ============================================
class CatListResponse(BaseModel):
    """Schema for list of cats with pagination"""
    
    cats: list[CatResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "cats": [
                    {
                        "id": 1,
                        "firebase_uid": "user_abc",
                        "name": "Orange_Cat",
                        "breed": "Persian",
                        "weight": 3.5,
                        "size_category": "M",
                        "chest_cm": 44.6,
                        "confidence": 0.95,
                        "image_url": "https://...",
                        "detected_at": "2025-02-04T10:30:00Z"
                    }
                ],
                "total": 10,
                "skip": 0,
                "limit": 100
            }
        }