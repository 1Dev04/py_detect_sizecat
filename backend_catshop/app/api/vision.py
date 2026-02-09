# Vision


import requests
from fastapi import APIRouter, HTTPException
from app.services.detect_cat import detect_cat
from app.services.analysis_cat import analyze_cat
from fastapi import APIRouter

router = APIRouter()

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


    detect = detect_cat(image_path)
    if not detect["is_cat"]:
        return {
            "is_cat": False,
            "confidence": 0.0,
            "message": "Not a cat"
        }

    analysis = analyze_cat(image_path, detect["bounding_box"])

    # 4️⃣ response (ตรงกับ Flutter CatData)
    return {
        "is_cat": True,
        "confidence": detect["confidence"],
        "bounding_box": detect["bounding_box"],
        "image_url": image_url,
        **analysis
    }
