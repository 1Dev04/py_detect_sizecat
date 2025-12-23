from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np 
from PIL import Image
import io
import requests
from datetime import datetime
from ultralytics import YOLO
from typing import Optional
import hashlib
import hmac
import time
import uuid
from dotenv import load_dotenv
import os

#main
app = FastAPI(title="Cat Detection & Clothing Recommendation API")

# COR Configuration 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load env variables
load_dotenv() 

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

CLOUDINARY_CONFIG = {
    'cloud_name': os.getenv('CLOUDINARY_NAME'),
    'api_key': os.getenv('CLOUDINARY_API_KEY'),
    'api_secret': os.getenv('CLOUDINARY_API_SECRET')
}

# Load YOLO cat_size_best model 
print("🔄 Loading YOLO model...")
model = YOLO(os.getenv('YOLO_MODEL_PATH'))
print("✅ YOLO model loaded!")

# ========================================
# DATABASE FUNCTIONS
# ========================================

def get_db_connection():
    """สร้างการเชื่อมต่อ Database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None
    
def create_processing_status(cloudinary_url: str, public_id: str) -> int:
    """สร้าง Status Record"""
    connection = get_db_connection()
    if not connection:
        raise Exception("Cannot connect to database")
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO processing_status 
        (cloudinary_url, public_id, status, created_at)
        VALUES (%s, %s, 'pending', %s)
        """
        cursor.execute(query, (cloudinary_url, public_id, datetime.now()))
        connection.commit()
        return cursor.lastrowid
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_processing_status(status_id: int, status: str, error_message: str = None):
    """อัปเดต Status"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        query = """
        UPDATE processing_status 
        SET status = %s, error_message = %s, updated_at = %s
        WHERE id = %s
        """
        cursor.execute(query, (status, error_message, datetime.now(), status_id))
        connection.commit()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
def save_cat_to_db(cat_data, cloudinary_url: str, status_id: int):
    """บันทึกข้อมูลแมวลงฐานข้อมูล"""
    connection = get_db_connection()
    if not connection:
        raise Exception("Cannot connect to database")
    
    try:
        cursor = connection.cursor()
        
        query = """
        INSERT INTO cats 
        (name, breed, age, weight, size_category, width_cm, height_cm, 
         confidence, image_path, detected_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            cat_data.get('name'),
            cat_data.get('breed', 'Unknown'),
            cat_data.get('age'),
            cat_data.get('weight'),
            cat_data.get('size_category'),
            cat_data.get('width_cm'),
            cat_data.get('height_cm'),
            cat_data.get('confidence'),
            cloudinary_url,
            datetime.now()
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        cat_id = cursor.lastrowid
        
        # อัปเดต status_id ใน processing_status
        cursor.execute(
            "UPDATE processing_status SET cat_id = %s WHERE id = %s",
            (cat_id, status_id)
        )
        connection.commit()
        
        return cat_id
        
    except Error as e:
        print(f"❌ Database error: {e}")
        raise
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ========================================
# DETECTION FUNCTIONS
# ========================================

def download_image_from_url(url: str):
    """ดาวน์โหลดรูปภาพจาก URL"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # ตรวจสอบขนาดไฟล์
        content_length = len(response.content)
        if content_length > int(os.getenv('MAX_FILE_SIZE', 10485760)):  # 10MB
            raise ValueError("Image too large (max 10MB)")
        
        # แปลงเป็น numpy array
        img_array = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Cannot decode image")
        
        return img
    except Exception as e:
        raise Exception(f"Download error: {str(e)}")
    
def detect_cat_color(img, bbox):
    """ตรวจจับสีหลักของแมว"""
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    cat_region = img[y1:y2, x1:x2]
    
    if cat_region.size == 0:
        return "unknown"
    
    cat_rgb = cv2.cvtColor(cat_region, cv2.COLOR_BGR2RGB)
    cat_small = cv2.resize(cat_rgb, (50, 50))
    pixels = cat_small.reshape(-1, 3)
    avg_color = np.mean(pixels, axis=0)
    
    return classify_color(avg_color)

def classify_color(rgb):
    """จัดหมวดหมู่สีจากค่า RGB"""
    r, g, b = rgb
    rgb_normalized = np.uint8([[rgb]])
    hsv = cv2.cvtColor(rgb_normalized, cv2.COLOR_RGB2HSV)[0][0]
    h, s, v = hsv
    
    if v < 50:
        return "black"
    if s < 30:
        return "white" if v > 180 else "gray"
    if h < 15 or h > 165:
        return "orange" if (r > 150 and g > 100) else "brown"
    elif h < 40:
        return "orange"
    elif h < 85:
        return "cream"
    else:
        return "gray"
    
def estimate_weight_from_size(width_cm, height_cm):
    """ประมาณน้ำหนักจากขนาด"""
    avg_size = (width_cm + height_cm) / 2
    if avg_size < 20:
        return np.random.uniform(1.0, 2.5)
    elif avg_size < 35:
        return np.random.uniform(2.5, 4.5)
    elif avg_size < 50:
        return np.random.uniform(4.5, 6.5)
    else:
        return np.random.uniform(6.5, 10.0)
    
def categorize_size(width_cm, height_cm):
    """จัดหมวดหมู่ขนาดแมว"""
    avg_size = (width_cm + height_cm) / 2
    if avg_size < 20:
        return "Small"
    elif avg_size < 35:
        return "Medium"
    elif avg_size < 50:
        return "Large"
    else:
        return "Extra Large"
    
def detect_and_process_cat(img):
    """ตรวจจับและประมวลผลแมว"""
    results = model(img, conf=float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.5')))
    cat_detections = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            if int(box.cls[0]) == 15:  # cat class
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                
                # ตรวจจับสีแมว
                cat_color = detect_cat_color(img, [x1, y1, x2, y2])
                
                # คำนวณขนาด
                width_px = x2 - x1
                height_px = y2 - y1
                
                scaling_factor = 0.1
                estimated_width_cm = width_px * scaling_factor
                estimated_height_cm = height_px * scaling_factor
                estimated_weight = estimate_weight_from_size(
                    estimated_width_cm, estimated_height_cm
                )
                
                cat_detections.append({
                    'confidence': confidence,
                    'color': cat_color,  # ← ✅ เพิ่มบรรทัดนี้!
                    'name': f"cat_{cat_color}",
                    'width_cm': round(estimated_width_cm, 2),
                    'height_cm': round(estimated_height_cm, 2),
                    'estimated_weight': round(estimated_weight, 2),
                    'size_category': categorize_size(estimated_width_cm, estimated_height_cm)
                })
    
    return cat_detections

def get_clothing_recommendations(size_category: str, weight: float):
    """แนะนำเสื้อผ้า"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, clothing_name, size_category, min_weight, max_weight, 
               price, stock
        FROM cat_clothing
        WHERE size_category = %s 
        AND (min_weight <= %s AND max_weight >= %s)
        AND stock > 0
        ORDER BY price ASC
        """
        cursor.execute(query, (size_category, weight, weight))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ========================================
# API ENDPOINTS
# ========================================

@app.get("/")
def read_root():
    return {
        "message": "Cat Detection API - Improved Version",
        "version": "3.0",
        "features": [
            "Real-time Processing",
            "Status Tracking",
            "Error Handling",
            "Security"
        ],
        "endpoints": {
            "process": "POST /api/process-cat",
            "status": "GET /api/status/{status_id}",
            "cats": "GET /api/cats",
            "signature": "POST /api/cloudinary-signature"
        }
    }

@app.post("/api/cloudinary-signature")
def generate_cloudinary_signature(timestamp: int = Body(...)):
    """
    สร้าง Signature สำหรับ Cloudinary Upload (ปลอดภัย)
    Flutter เรียก API นี้ก่อน Upload
    """
    try:
        # สร้าง signature
        params_to_sign = f"timestamp={timestamp}&upload_preset=your_preset"
        signature = hmac.new(
            CLOUDINARY_CONFIG['api_secret'].encode('utf-8'),
            params_to_sign.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        return {
            "success": True,
            "signature": signature,
            "timestamp": timestamp,
            "api_key": CLOUDINARY_CONFIG['api_key'],
            "cloud_name": CLOUDINARY_CONFIG['cloud_name']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/process-cat")
def process_cat_immediately(
    cloudinary_url: str = Body(...),
    public_id: str = Body(...)
):
    """ประมวลผลแมวทันที"""
    status_id = None
    
    try:
        # 1-4. สร้าง status, ดาวน์โหลด, ตรวจจับ (เหมือนเดิม)
        status_id = create_processing_status(cloudinary_url, public_id)
        update_processing_status(status_id, 'processing')
        
        print(f"📥 Downloading image from Cloudinary...")
        img = download_image_from_url(cloudinary_url)
        
        print(f"🔍 Detecting cat...")
        detections = detect_and_process_cat(img)
        
        if not detections:
            update_processing_status(status_id, 'failed', 'No cat detected')
            return {
                "success": False,
                "message": "ไม่พบแมวในรูปภาพ",
                "status_id": status_id,
                "data": None
            }
        
        # 5. เอาแมวที่มี confidence สูงสุด
        main_cat = max(detections, key=lambda x: x['confidence'])
        
        # 6. สร้างชื่อไม่ซ้ำ
        unique_id = uuid.uuid4().hex[:8]
        cat_name = f"cat_{main_cat['color']}_{unique_id}"  # ← ✅ ตอนนี้ใช้งานได้แล้ว!
        
        cat_data = {
            'name': cat_name,  # เช่น "cat_orange_a3f7b2e1"
            'breed': 'Unknown',
            'age': None,
            'weight': main_cat['estimated_weight'],
            'size_category': main_cat['size_category'],
            'width_cm': main_cat['width_cm'],
            'height_cm': main_cat['height_cm'],
            'confidence': main_cat['confidence']
        }
        
        # 7-9. บันทึก database, อัปเดตสถานะ, ดึงคำแนะนำ (เหมือนเดิม)
        print(f"💾 Saving to database...")
        cat_id = save_cat_to_db(cat_data, cloudinary_url, status_id)
        
        update_processing_status(status_id, 'completed')
        
        clothing_recommendations = get_clothing_recommendations(
            main_cat['size_category'],
            main_cat['estimated_weight']
        )
        
        print(f"✅ Processing completed! Cat: {cat_name}")
        
        return {
            "success": True,
            "message": "ตรวจจับแมวสำเร็จ",
            "status_id": status_id,
            "data": {
                "cat": {
                    "id": cat_id,
                    "name": cat_name,
                    "color": main_cat['color'],  # ← ✅ ส่งสีกลับไปด้วย
                    "breed": "Unknown",
                    "size_category": main_cat['size_category'],
                    "width_cm": main_cat['width_cm'],
                    "height_cm": main_cat['height_cm'],
                    "estimated_weight": main_cat['estimated_weight'],
                    "confidence": round(main_cat['confidence'] * 100, 2),
                    "image_url": cloudinary_url
                },
                "clothing_recommendations": clothing_recommendations,
                "total_cats_detected": len(detections)
            }
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if status_id:
            update_processing_status(status_id, 'failed', str(e))
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "status_id": status_id
            }
        )
    
@app.get("/api/status/{status_id}")
def get_processing_status(status_id: int):
    """ตรวจสอบสถานะการประมวลผล"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT ps.*, c.id as cat_id, c.name as cat_name
        FROM processing_status ps
        LEFT JOIN cats c ON ps.cat_id = c.id
        WHERE ps.id = %s
        """
        cursor.execute(query, (status_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Status not found")
        
        return {
            "success": True,
            "data": result
        }
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/api/cats")
def get_all_cats(limit: Optional[int] = 100, offset: Optional[int] = 0):
    """ดึงข้อมูลแมวทั้งหมด"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, name, breed, age, weight, size_category, 
               width_cm, height_cm, confidence, image_path, detected_at
        FROM cats
        ORDER BY detected_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()
        
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/api/cats/{cat_id}")
def get_cat_by_id(cat_id: int):
    """ดึงข้อมูลแมวตาม ID"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, name, breed, age, weight, size_category,
               width_cm, height_cm, confidence, image_path, detected_at
        FROM cats
        WHERE id = %s
        """
        cursor.execute(query, (cat_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Cat not found")
        
        return {
            "success": True,
            "data": result
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/api/cats/{cat_id}/recommendations")
def get_cat_clothing_recommendations(cat_id: int):
    """แนะนำเสื้อผ้าสำหรับแมว"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT size_category, weight FROM cats WHERE id = %s"
        cursor.execute(query, (cat_id,))
        cat = cursor.fetchone()
        
        if not cat:
            raise HTTPException(status_code=404, detail="Cat not found")
        
        recommendations = get_clothing_recommendations(
            cat['size_category'],
            cat['weight']
        )
        
        return {
            "success": True,
            "cat_id": cat_id,
            "size_category": cat['size_category'],
            "weight": cat['weight'],
            "recommendations": recommendations
        }
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)