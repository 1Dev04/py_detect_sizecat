from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
from PIL import Image
import io
from dotenv import load_dotenv
import os
from datetime import datetime
from ultralytics import YOLO
from typing import Optional, List
import uuid


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

UPLOAD_DIR = "uploaded_images"
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

# Load YOLO cat_size_best model 
model = YOLO('yolov8n.pt') 

def get_db_connection():
    ""' เชื่อมต่อ Database '""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None
    
def save_image(image_bytes, filename: str) -> str:
    """บันทึกรูปภาพลง file system"""
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return filepath

def estimate_weight_from_size(width_cm, height_cm):
    """  ประมาณน้ำหนักแมวจากขนาด """
    avg_size = (width_cm + height_cm) / 2
    if avg_size < 20 :
        return np.random.uniform(1.0, 2.5)  # ลูกแมว
    elif avg_size < 30:
        return np.random.uniform(2.5, 4.5)  # แมววัยรุ่น
    elif avg_size < 50:
        return np.random.uniform(4.5, 6.5)  # แมวโต
    else:
        return np.random.uniform(6.5, 10.0)  # แมวใหญ่ 
    
def categorize_size(width_cm, height_cm):
    """  จัดหมวดหมู่ขนาดแมว """
    avg_size = (width_cm + height_cm) / 2

    if avg_size < 20 :
        return "Small"
    elif avg_size < 30:
        return "Medium"
    elif avg_size < 50:
        return "Large"
    else: 
        return "Extra Large"
    
def detect_cat_size(image_bytes):
    """ 
        ตรวจจับแมวเเละวัดขนาด
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None, "Invalid image data"
    
    # Check YOLO 
    results = model(img, conf=0.5)

    cat_detection = []

    for result in results:
        boxes = result.boxes
        for box in boxes:
            if int(box.cls[0]) == 15:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])

                # Pixel size cal
                width_px = x2 - x1
                height_px = y2 - y1

                # สมมติว่า 1 พิกเซล = 0.26458 มม. (ขึ้นอยู่กับการตั้งค่ากล้อง)
                scaling_factor = 0.26458
                estimated_width_cm = width_px * scaling_factor
                estimated_height_cm = height_px * scaling_factor


                estimated_weight  = estimate_weight_from_size(
                    estimated_width_cm,
                    estimated_height_cm
                )

                cat_detection.append({
                    'confidence': confidence,
                    'bbox': [
                        float(x1),
                        float(y1),
                        float(x2),
                        float(y2)
                    ],
                    'width_cm': round(estimated_width_cm, 2),
                    'height_cm': round(estimated_height_cm, 2),
                    'estimated_weight': round(estimated_weight, 2),
                    'size_category': categorize_size(estimated_width_cm, estimated_height_cm)
                })
        
        return cat_detection
    
def save_cat_to_db(cat_data, image_path: str):
    """บันทึกข้อมูลแมวลงฐานข้อมูล"""
    connection = get_db_connection()
    if not connection:
        raise Exception("Cannot connect to database")
    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO cats 
            (name, breed, age, weight, size_category,
                width_cm, height_cm, confidence, image_path, detected_at)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)   
        """

        values = (
            cat_data.get('name', 'Unknown Cat'),
            cat_data.get('breed', 'Unknown'),
            cat_data.get('age'),
            cat_data.get('weight'),
            cat_data.get('size_category'),
            cat_data.get('width_cm'),
            cat_data.get('height_cm'),
            cat_data.get('confidence'),
            image_path,
            datetime.now()
        )

        cursor.execute(query, values)
        connection.commit()

        cat_id = cursor.lastrowid
        return cat_id
    
    except Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_clothing_recommen(size_category: str, weight: float):
    """ แนะนำเสื้อผ้าสำหรับแมว """
    connection = get_db_connection()

    if not connection:
        return []

    # try:
    #     cursor = connection.cursor(dictionary=True)

    #     query = """

    #     """