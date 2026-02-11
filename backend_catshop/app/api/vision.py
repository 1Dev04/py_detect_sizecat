from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import requests
import os
from pathlib import Path
import uuid
from app.auth.dependencies import verify_firebase_token
from app.services.detect_cat import detect_cat
from app.services.analysis_cat import analyze_cat

router = APIRouter()

# ============================================
# REQUEST SCHEMA
# ============================================
class AnalyzeCatRequest(BaseModel):
    """Schema สำหรับ request วิเคราะห์แมว"""
    image_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://res.cloudinary.com/.../cat.jpg"
            }
        }


# ============================================
# ANALYZE CAT ENDPOINT
# ============================================
@router.post("/vision/analyze-cat", response_model=dict)
async def analyze_cat_endpoint(
    request: AnalyzeCatRequest,
    user: dict = Depends(verify_firebase_token)
):
    """
    🐱 **วิเคราะห์แมวจากรูปภาพ**
    
    **ขั้นตอน:**
    1. ดาวน์โหลดรูปภาพจาก URL
    2. ตรวจจับแมวด้วย YOLO (detect_cat)
    3. วิเคราะห์ขนาดแมวด้วย CatAnalyzer (analyze_cat)
    4. ส่งผลกลับในรูปแบบที่ Flutter ต้องการ
    
    **Authentication:** Firebase ID Token required
    
    **Request Body:**
```json
    {
        "image_url": "https://res.cloudinary.com/.../cat.jpg"
    }
```
    
    **Response:**
```json
    {
        "is_cat": true,
        "confidence": 0.87,
        "message": "✅ พบแมวในภาพแล้ว!",
        "name": "orange_white",
        "breed": "domestic_shorthair",
        "age": null,
        "weight": 4.5,
        "size_category": "M",
        "chest_cm": 35.5,
        "neck_cm": 22.0,
        "body_length_cm": 45.0,
        "bounding_box": [100, 150, 400, 450],
        "image_url": "...",
        "thumbnail_url": null,
        "detected_at": "2025-02-11T10:30:00Z"
    }
```
    """
    
    try:
        # 🔐 ดึง firebase_uid จาก token
        firebase_uid = user.get("uid")
        
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )
        
        print(f"\n🔍 Starting analysis for user: {firebase_uid[:8]}***")
        print(f"📸 Image URL: {request.image_url}")
        
        # ========================================
        # STEP 1: Download Image
        # ========================================
        print("\n--- STEP 1: Downloading Image ---")
        
        try:
            response = requests.get(request.image_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to download image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot download image: {str(e)}"
            )
        
        # สร้าง temp directory
        temp_dir = Path("/tmp/cat_images")
        temp_dir.mkdir(exist_ok=True)
        
        # สร้างชื่อไฟล์ชั่วคราวที่ไม่ซ้ำกัน
        temp_filename = f"cat_{uuid.uuid4()}.jpg"
        temp_path = temp_dir / temp_filename
        
        # บันทึกรูปภาพ
        with open(temp_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Image saved to: {temp_path}")
        print(f"📦 Image size: {len(response.content) / 1024:.2f} KB")
        
        try:
            # ========================================
            # STEP 2: Detect Cat (YOLO)
            # ========================================
            print("\n--- STEP 2: Detecting Cat with YOLO ---")
            
            detect_result = detect_cat(str(temp_path))
            
            print(f"🔍 Detection Result:")
            print(f"   - is_cat: {detect_result.get('is_cat')}")
            print(f"   - confidence: {detect_result.get('confidence')}")
            print(f"   - bounding_box: {detect_result.get('bounding_box')}")
            
            # ถ้าไม่พบแมว
            if not detect_result.get("is_cat"):
                print("❌ No cat detected in image")
                return {
                    "is_cat": False,
                    "confidence": detect_result.get("confidence", 0.0),
                    "message": "😿 ไม่พบแมวในภาพ กรุณาถ่ายรูปใหม่"
                }
            
            print("✅ Cat detected!")
            
            # ========================================
            # STEP 3: Analyze Cat Size
            # ========================================
            print("\n--- STEP 3: Analyzing Cat Size ---")
            
            bounding_box = detect_result["bounding_box"]
            
            analysis_result = analyze_cat(
                image_path=str(temp_path),
                bounding_box=bounding_box,
                firebase_uid=firebase_uid,
                cat_color=None,  # จะถูก detect อัตโนมัติ
                breed="unknown",
                age_category="adult"
            )
            
            print(f"📊 Analysis Result:")
            print(f"   - cat_color: {analysis_result.get('cat_color')}")
            print(f"   - weight_kg: {analysis_result.get('weight_kg')}")
            print(f"   - size_category: {analysis_result.get('size_category')}")
            print(f"   - confidence: {analysis_result.get('confidence')}")
            
            # ========================================
            # STEP 4: Format Response for Flutter
            # ========================================
            print("\n--- STEP 4: Formatting Response ---")
            
            measurements = analysis_result.get('measurements', {})
            
            response_data = {
                # ✅ Detection info
                "is_cat": True,
                "confidence": float(detect_result.get("confidence", 0.0)),
                "message": "✅ พบแมวในภาพแล้ว!",
                
                # ✅ CatData fields (ตรงกับ Flutter)
                "name": analysis_result.get("cat_color", "Unknown"),  # Flutter ใช้ 'name' สำหรับสี
                "breed": analysis_result.get("breed", None),
                "age": None,  # ไม่สามารถ detect อายุจากรูปได้
                "weight": float(analysis_result.get("weight_kg", 0.0)),
                "size_category": analysis_result.get("size_category", "Unknown"),
                
                # ✅ Measurements (แกะออกจาก dict)
                "chest_cm": float(measurements.get("chest_cm", 0.0)),
                "neck_cm": float(measurements.get("neck_cm", 0.0)) if measurements.get("neck_cm") else None,
                "body_length_cm": float(measurements.get("body_length_cm", 0.0)) if measurements.get("body_length_cm") else None,
                
                # ✅ Additional info
                "bounding_box": bounding_box,
                "image_url": request.image_url,
                "thumbnail_url": None,  # ยังไม่มี thumbnail
                "detected_at": datetime.utcnow().isoformat() + "Z",
                
                # 🔥 Extra: ข้อมูลเพิ่มเติม (ไม่บังคับ)
                "analysis_details": {
                    "posture": analysis_result.get("posture"),
                    "quality_flag": analysis_result.get("quality_flag"),
                    "body_condition": analysis_result.get("body_condition"),
                    "body_condition_score": analysis_result.get("body_condition_score"),
                    "bmi": analysis_result.get("bmi"),
                    "size_recommendation": analysis_result.get("size_recommendation"),
                    "all_measurements": measurements
                }
            }
            
            print("✅ Response formatted successfully")
            print(f"\n🎉 Analysis completed for user {firebase_uid[:8]}***")
            
            return response_data
            
        finally:
            # ========================================
            # CLEANUP: ลบไฟล์ชั่วคราว
            # ========================================
            if temp_path.exists():
                temp_path.unlink()
                print(f"🗑️ Cleaned up temp file: {temp_path}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )