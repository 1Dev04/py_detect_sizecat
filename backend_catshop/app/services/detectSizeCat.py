# app/services/detectSizeCat.py
import cv2
import numpy as np
import requests
from ultralytics import YOLO
from typing import Dict, Any
import os 
from dotenv import load_dotenv
from typing import List
# Load ENV + Model
load_dotenv()


MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "models/cat_size_yolo.pt")
model = YOLO(MODEL_PATH)


SIZE_CHART = {
    "XS": {"min_w": 0.5, "max_w": 1.5, "chest": (28, 32)},
    "S":  {"min_w": 1.5, "max_w": 3.0, "chest": (32, 36)},
    "M":  {"min_w": 3.0, "max_w": 4.5, "chest": (36, 40)},
    "L":  {"min_w": 4.5, "max_w": 6.0, "chest": (40, 44)},
    "XL": {"min_w": 6.0, "max_w": 99,  "chest": (44, 50)},
}

# Helpers 

def infer_size(weight: float, chest: float) -> str:
    for size, r in SIZE_CHART.items():
        if r["min_w"] <= weight < r["max_w"] and r["chest"][0] <= chest <= r["chest"][1]:
            return size
    return "XL"

def estimate_age(size: str) -> int | None:
  
    return {
        "XS": 3,
        "S": 6,
        "M": 12,
        "L": 24,
        "XL": 36
    }.get(size)

def detect_colors(img: np.ndarray, bounding_box: List[float]) -> List[str]:
    x1, y1, x2, y2 = map(int, bounding_box)
    crop = img[y1:y2, x1:x2]

    if crop.size == 0:
        return ["unknown"]
    
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    avg_hsv = np.mean(hsv.reshape(-1, 3), axis=0)
    h, s, v = avg_hsv

    if v < 50:
        return ["black"]
    if h < 15:
        return ["orange"]
    if 15 <= h < 35:
        return ["yellow"]
    if s < 40:
        return ["white"]
    
    return ["mixed"]

def generate_cat_name(colors: List[str]) -> str:
    return "cat_" + "_".join(colors)

# Main Detection
def detect_cat_from_url(image_url: str) -> Dict[str, Any] | None:
    # Load image from Cloudinary
    resp = requests.get(image_url, timeout=10)
    if resp.status_code != 200:
        raise Exception("Cannot download image")

    img_array = np.frombuffer(resp.content, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise Exception("Invalid image")

    # YOLO detect
    results = model(img, conf=0.4)

    r = results[0]

    if r.boxes is None or len(r.boxes) == 0:
        return None

    box = r.boxes[0]
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    confidence = float(box.conf[0])

    h, w = img.shape[:2]

    chest_cm = round((x2 - x1) / w * 100, 2)
    body_length_cm = round((y2 - y1) / h * 100, 2)
    neck_cm = round(chest_cm * 0.6, 2)

    # mock weight (v1)
    weight_est = round(chest_cm / 10, 2)

    size = infer_size(weight_est, chest_cm)
    age_est = estimate_age(size)

    colors = detect_colors(img, [x1, y1, x2, y2])
    name = generate_cat_name(colors)

    return {
        "name": name,
        "breed": "domestic",   # v1 default
        "age": age_est,

        "weight": weight_est,
        "size_category": size,

        "chest_cm": chest_cm,
        "neck_cm": neck_cm,
        "body_length_cm": body_length_cm,

        "confidence": confidence,
        "bounding_box": [x1, y1, x2, y2],

        "color_tags": colors
    }