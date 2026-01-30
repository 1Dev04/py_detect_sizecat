from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CatBase(BaseModel):
    """Base schema for Cat"""
    cat_color: Optional[str] = Field(None, max_length=100, description="สีแมว")
    breed: Optional[str] = Field(None, max_length=50, description="สายพันธุ์")
    age: Optional[int] = Field(None, ge=0, le=30)
    weight: float = Field(..., gt=0, le=50)
    size_category: str = Field(..., pattern="^(XS|S|M|L|XL)$")
    chest_cm: float = Field(..., gt=0, le=200)
    neck_cm: Optional[float] = Field(None, gt=0, le=100)
    body_length_cm: Optional[float] = Field(None, gt=0, le=200)
    confidence: float = Field(..., ge=0, le=1)
    image_url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)


class CatCreate(CatBase):
    """Schema for creating a cat"""
    pass


class CatUpdate(BaseModel):
    """Schema for updating a cat (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    breed: Optional[str] = Field(None, max_length=50)
    age: Optional[int] = Field(None, ge=0, le=30)
    weight: Optional[float] = Field(None, gt=0, le=50)
    size_category: Optional[str] = Field(None, pattern="^(XS|S|M|L|XL)$")
    chest_cm: Optional[float] = Field(None, gt=0, le=200)
    neck_cm: Optional[float] = Field(None, gt=0, le=100)
    body_length_cm: Optional[float] = Field(None, gt=0, le=200)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    image_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)


class CatResponse(CatBase):
    """Schema for cat response"""
    id: int
    detected_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CatDetectRequest(BaseModel):
    """Schema for cat detection request (from ChatGPT Vision)"""
    image_url: str


class CatDetectResponse(BaseModel):
    """Schema for cat detection response"""
    is_cat: bool
    is_cartoon: bool = False
    is_blur: bool = False
    is_dark: bool = False
    distance: str = "medium"  # "close", "medium", "far"
    confidence: float


class CatPredictRequest(BaseModel):
    """Schema for cat prediction request"""
    image_url: str


class CatPredictResponse(BaseModel):
    """Schema for cat prediction response"""
    name: str = "Unknown Cat"
    breed: str
    weight_estimate: str
    age_estimate: str
    color: str
    size_category: str
    chest_cm: float
    neck_cm: Optional[float] = None
    body_length_cm: Optional[float] = None
    description: str
    confidence: float