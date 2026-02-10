"""Cat Detect Service with YOLOv8 Nano - Fixed for PyTorch 2.6+"""

import cv2
import numpy as np
import torch
import os
from ultralytics import YOLO
from typing import Dict

# 🔥 FIX: PyTorch 2.6+ weights_only issue
os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'


class CatDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        print(f"🔥 Loading YOLO model: {model_path}")
        self.model = YOLO(model_path, verbose=False)
        self.cat_class_id = 15
        print("✅ YOLO model loaded successfully")

    def check_image_quality(self, image: np.ndarray) -> Dict:
        h, w = image.shape[:2]
        
        if w < 100 or h < 100:
            return {"is_valid": False, "reason": "รูปเล็กเกินไป"}
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var < 50:
            return {"is_valid": False, "reason": "รูปเบลอ"}
        
        mean_brightness = np.mean(gray)
        if mean_brightness < 30 or mean_brightness > 225:
            return {"is_valid": False, "reason": "ความสว่างไม่เหมาะ"}
        
        return {"is_valid": True, "reason": None}

    def detect_cat(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"is_cat": False, "confidence": 0.0, "bounding_box": None, "error": "โหลดภาพไม่ได้"}

            quality = self.check_image_quality(image)
            if not quality["is_valid"]:
                return {"is_cat": False, "confidence": 0.0, "bounding_box": None, "error": quality["reason"]}

            results = self.model(image, conf=confidence_threshold, verbose=False)

            cats = []
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) == self.cat_class_id:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cats.append({
                            "confidence": float(box.conf[0]),
                            "bbox": [int(x1), int(y1), int(x2), int(y2)]
                        })

            if not cats:
                return {"is_cat": False, "confidence": 0.0, "bounding_box": None, "error": "ไม่พบแมว"}

            best = max(cats, key=lambda x: x["confidence"])
            return {
                "is_cat": True,
                "confidence": round(best["confidence"], 2),
                "bounding_box": best["bbox"],
                "total_cats_detected": len(cats),
                "error": None
            }

        except Exception as e:
            print(f"❌ detect_cat error: {e}")
            return {"is_cat": False, "confidence": 0.0, "bounding_box": None, "error": str(e)}


_detector_instance = None

def get_detector() -> CatDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CatDetector()
    return _detector_instance

def detect_cat(image_path: str) -> Dict:
    return get_detector().detect_cat(image_path)
