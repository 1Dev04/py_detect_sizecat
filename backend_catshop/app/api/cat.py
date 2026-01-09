from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional
from app.services.detectSizeCat import detect_cat_from_url

router = APIRouter(
    prefix="/api/cat",
    tags=["Cat AI"]
)

# Request Schema
class DetectCatRequest(BaseModel):
    image_url: HttpUrl 


# Reponse Schema
class DetectCatResponse(BaseModel):
    name: str
    breed: Optional[str]
    age: Optional[int]

    weight: float
    size_category: str

    chest_cm: float
    neck_cm: Optional[float]
    body_length_cm: Optional[float]

    confidence: float
    bounding_box: List[float]

    image_url: str
    thumbnail_url: Optional[str]
    detected_at: datetime
   
# API Endpoint

@router.post("/detect", response_model=DetectCatResponse)
def detect_cat(payload: DetectCatRequest):
    """ Fetch image_url from Cloudinary 
    → AI detect & predict
    → return cat attributes (ยังไม่ save DB)
    """

    try: 
        result = detect_cat_from_url(payload.image_url)

        if result is None: 
            raise HTTPException(
                status_code=404,
                detail="No cat detected in image"
            )
        
        return {
            "name": result["name"],
            "breed": result.get("breed"),
            "age": result.get("age"),

            "weight": result["weight"],
            "size_category": result["size_category"],

            "chest_cm": result["chest_cm"],
            "neck_cm": result.get("neck_cm"),
            "body_length_cm": result.get("body_length_cm"),

            "confidence": result["confidence"],
            "bounding_box": result["bounding_box"],

            "image_url": payload.image_url,
            "thumbnail_url": payload.image_url,  # ใช้ Cloudinary transform ทีหลังได้
            "detected_at": datetime.utcnow()
        }

    except HTTPException:
        raise 

    except Exception as e: 
        raise HTTPException(
            status_code=500,
            detail=f"Detection failed: {str(e)}"
        )