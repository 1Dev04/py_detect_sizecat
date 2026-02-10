""" Cat Detect Service with YOLOv8 Nona"""



import cv2
import numpy as np
from ultralytics import YOLO
from typing import Dict


class CatDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        print(f"🔥 Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.cat_class_id = 15  # class 15 = cat in COCO dataset

    def check_image_quality(self, image: np.ndarray) -> Dict[str, any]:
        """ตรวจสอบคุณภาพรูปภาพ"""
        h, w = image.shape[:2]
        
        # ตรวจสอบขนาดรูป
        if w < 100 or h < 100:
            return {
                "is_valid": False,
                "reason": "รูปภาพเล็กเกินไป (ต้องมากกว่า 100x100 pixels)"
            }
        
        # ตรวจสอบความคมชัด (Laplacian variance)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var < 50:
            return {
                "is_valid": False,
                "reason": "รูปภาพเบลอเกินไป"
            }
        
        # ตรวจสอบความสว่าง
        mean_brightness = np.mean(gray)
        if mean_brightness < 30 or mean_brightness > 225:
            return {
                "is_valid": False,
                "reason": "ความสว่างไม่เหมาะสม (มืดหรือสว่างเกินไป)"
            }
        
        return {
            "is_valid": True,
            "reason": None,
            "sharpness": round(laplacian_var, 2),
            "brightness": round(mean_brightness, 2)
        }

    def detect_cat(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """
        ตรวจจับแมวในรูปภาพด้วย YOLOv8
        
        Returns:
            Dict with keys: is_cat, confidence, bounding_box, error
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    "is_cat": False,
                    "confidence": 0.0,
                    "bounding_box": None,
                    "error": "ไม่สามารถโหลดภาพได้"
                }

            # Check image quality
            quality = self.check_image_quality(image)
            if not quality["is_valid"]:
                return {
                    "is_cat": False,
                    "confidence": 0.0,
                    "bounding_box": None,
                    "quality_check": quality,
                    "error": f"คุณภาพไม่ผ่านเกณฑ์: {quality['reason']}"
                }

            # Run YOLO detection
            results = self.model(image, conf=confidence_threshold, verbose=False)

            # Find cat detections
            cat_detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    if class_id == self.cat_class_id:
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cat_detections.append({
                            "confidence": conf,
                            "bbox": [int(x1), int(y1), int(x2), int(y2)]  # 🔥 ส่งเป็น [x1,y1,x2,y2]
                        })

            # No cat found
            if not cat_detections:
                return {
                    "is_cat": False,
                    "confidence": 0.0,
                    "bounding_box": None,
                    "quality_check": quality,
                    "error": "ไม่พบแมวในภาพ กรุณาถ่ายภาพแมวให้ชัดเจน"
                }

            # Choose cat with highest confidence
            best_cat = max(cat_detections, key=lambda x: x["confidence"])

            return {
                "is_cat": True,
                "confidence": round(best_cat["confidence"], 2),
                "bounding_box": best_cat["bbox"],  # [x1, y1, x2, y2]
                "quality_check": quality,
                "total_cats_detected": len(cat_detections),
                "error": None
            }

        except Exception as e:
            import traceback
            print(f"❌ Error in detect_cat: {e}")
            print(traceback.format_exc())
            return {
                "is_cat": False,
                "confidence": 0.0,
                "bounding_box": None,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }


# Singleton instance for FastAPI
_detector_instance = None


def get_detector() -> CatDetector:
    """Get or create detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CatDetector()
    return _detector_instance


def detect_cat(image_path: str) -> Dict:
    """Main function for calling from FastAPI"""
    detector = get_detector()
    return detector.detect_cat(image_path)