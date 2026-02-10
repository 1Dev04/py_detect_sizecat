# Vision


import requests

from app.services.detect_cat import detect_cat
from app.services.analysis_cat import analyze_cat
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth

router = APIRouter()

try:
    cred = credentials.Certificate("path/to/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"⚠️ Firebase Admin already initialized or error: {e}")


# ฟังก์ชันตรวจสอบ Firebase Token
def verify_firebase_token(authorization: Optional[str] = Header(None)):
    """
    ตรวจสอบ Firebase ID Token
    Returns: user_id (uid จาก Firebase)
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # ตรวจสอบ Token ด้วย Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        email = decoded_token.get('email', 'N/A')
        
        print(f"✅ Authenticated user: {user_id} ({email})")
        return user_id
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="Token revoked")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"❌ Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")



@router.post("/vision/analyze-cat")
def analyze_cat_url(payload: dict):
    image_url = payload.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")

    image_path = "/tmp/cat.jpg"
    r = requests.get(image_url, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Cannot download image")

    with open(image_path, "wb") as f:
        f.write(r.content)

    # 1️⃣ Detect Cat
    detect = detect_cat(image_path)
    if not detect["is_cat"]:
        return {
            "is_cat": False,
            "confidence": detect.get("confidence", 0.0),
            "message": "Not a cat (ไม่พบแมวในภาพ)"
        }

    analysis = analyze_cat(image_path, detect["bounding_box"])


    from datetime import datetime
    
    return {
        "is_cat": True,
        "confidence": detect["confidence"],
        "message": "Cat detected successfully",
        "name": analysis.get("name", "Unknown Cat"),  # สีแมว/ชื่อ
        "breed": analysis.get("breed", None),
        "age": analysis.get("age", None),
        "weight": analysis.get("weight", 0.0),
        "size_category": analysis.get("size_category", "Unknown"),
        "chest_cm": analysis.get("chest_cm", 0.0),
        "neck_cm": analysis.get("neck_cm", None),
        "body_length_cm": analysis.get("body_length_cm", None),
        "bounding_box": detect["bounding_box"],
        "image_url": image_url,
        "thumbnail_url": image_url,  # ใช้เดียวกันหรือสร้าง thumbnail
        "detected_at": datetime.utcnow().isoformat()
    }


