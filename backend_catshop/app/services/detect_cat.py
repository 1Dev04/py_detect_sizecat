""" Cat Detect Service with YOLOv8 Nona"""

import cv2 
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import torch
from typing import Dict, Tuple, Optional

class CatDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        print(f"🔥 Loading YOLO model: {model_path}") 
        self.model = YOLO(model_path)
        self.cat_class_id = 15  # class 15 = cat

    def check_image_quality(self, image: np.ndarray) -> Dict[str, any]:
        ...
    
    def detect_cat(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {
                    "is_cat": False,
                    "confidence": 0.0,
                    "error": "ไม่สามารถโหลดภาพได้"
                }

            quality = self.check_image_quality(image)
            if not quality["is_valid"]:
                return {
                    "is_cat": False,
                    "confidence": 0.0,
                    "quality_check": quality,
                    "error": f"คุณภาพไม่ผ่านเกณฑ์: {quality['reason']}"
                }

            results = self.model(image, conf=confidence_threshold, verbose=False)

            cat_detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    if class_id == self.cat_class_id:
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cat_detections.append({
                            "confidence": conf,
                            "bbox": {
                                "x": int(x1),
                                "y": int(y1),
                                "w": int(x2 - x1),
                                "h": int(y2 - y1)
                            }
                        })

            if not cat_detections:
                return {
                    "is_cat": False,
                    "confidence": 0.0,
                    "quality_check": quality,
                    "error": "ไม่พบแมวในภาพ กรุณาถ่ายภาพแมวให้ชัดเจน"
                }

            best_cat = max(cat_detections, key=lambda x: x["confidence"])

            return {
                "is_cat": True,
                "confidence": round(best_cat["confidence"], 2),
                "bounding_box": best_cat["bbox"],
                "quality_check": quality,
                "total_cats_detected": len(cat_detections),
                "error": None
            }

        except Exception as e:
            return {
                "is_cat": False,
                "confidence": 0.0,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }
    
def detect_cat(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
    """
        Check cat inside image
    """

    try:
        #  Load image
        image = cv2.imread(image_path)
        if image is None:
            return {
                "is_cat": False,
                "confidence": 0.0,
                "error": "ไม่สามารถโหลดภาพได้"
            }
        quality = self.check_image_quality(image)
        if not quality["is_valid"]:
            return {
                "is_cat": False,
                "confidence": 0.0,
                "quality_check": quality,
                "error": f"คุณภาพไม่ผ่านเกณฑ์: {quality['reason']}"
            }
        
        # Run YOLO detection 
        results = self.model(image, conf=confidence_threshold, verbose=False)

        # find cat from results

        cat_detections = []
        for result in results:
            boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls[0])
            if class_id == self.cat_class_id:
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cat_detections.append({
                    "confidence": conf,
                    "bbox": {
                        "x": int(x1),
                        "y": int(y1),
                        "w": int(x2 - x1),
                        "h": int(y2 - y1)
                    }
                })

                # not found cat
                if not cat_detections:
                    return {
                        "is_cat": False,
                        "confidence": 0.0,
                        "quality_check": quality,
                        "error": "ไม่พบแมวในภาพ กรุณาถ่ายภาพแมวให้ชัดเจน"
                    }
                
                # choose cat is confidence max
                best_cat = max(cat_detections, key=lambda x: x["confidence"])

                return {
                    "is_cat": True,
                    "confidence": round(best_cat["confidence"], 2),
                    "bounding_box": best_cat["bbox"],
                    "quality_check": quality,
                    "total_cats_detected": len(cat_detections),
                    "error": None
                }
    except Exception as e:
        return {
            "is_cat": False,
            "confidence": 0.0,
            "error": f"เกิดข้อผิดพลาด: {str(e)}"
        }
    
# Singletion instance for FastAPI
_detector_instance = None
 
def get_detector() -> CatDetector:
    """ Get or create detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CatDetector()
    return _detector_instance

def detect_cat(image_path: str) -> Dict:
    """ Main function calling FastAPI """
    detector  = get_detector()
    return detector.detect_cat(image_path)