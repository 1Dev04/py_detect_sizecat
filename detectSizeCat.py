from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector 
from mysql.connector import Error 
import cv2
import numpy as np
from PIL import Image 
import io
import base64
from datetime import datetime
from ultralytics import YOLO
import os
from dotenv import load_dotenv


#main
app = FastAPI(title="Cat Size Detection API")

# COR Configuration 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load env variables
load_dotenv() 

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Load YOLO model 
model = YOLO('runs/detect/train/weights/cat_size_best.pt') 

def get_db_connection():
    ""' สร้างการเชื่่อมต่อฐานข้อมูล MySQL '""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
    
def detect_cat_size(image_bytes):
     """
    ตรวจจับแมวและวัดขนาด
  
    """
     nparr = np.frombuffer(image_bytes, np.uint8)
     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

     if img is None: 
         raise ValueError("Cannot decode image")
     
     # Check YOLO model 
     results = model(img, conf=0.5)

     cat_detections  = []

     for result in results:
         boxes = result.boxes
         for box in boxes:
             if model.names[int(box.cls[0])] == "cat":
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])

                # Calculate size 
                width_px  = x2 - x1
                height_px  = y2 - y1
                scaling_factor = 0.1
                estimated_width_cm = width_px * scaling_factor
                estimated_height_cm = height_px * scaling_factor

                cat_detections.append({
                        'confidence': confidence,
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'width_px': float(width_px),
                        'height_px': float(height_px),
                        'width_cm': round(estimated_width_cm, 2),
                        'height_cm': round(estimated_height_cm, 2),
                        'size_category': categorize_size(estimated_width_cm, estimated_height_cm)
                })
                return cat_detections


def categorize_size(width_cm, height_cm):
    """ จัดหมวดหมู่ขนาดแมว """
    avg_size = (width_cm + height_cm) / 2 

    if avg_size < 20: 
        return "Small (ลูกแมว)"
    elif avg_size < 35:
        return "Medium (แมววัยรุ่น)"
    elif avg_size < 50:
        return "Large (แมวโต)"
    else:
        return "Extra Large (แมวใหญ่มาก ไม่มี size )"


def save_to_database(cat_data, image_bytes):
    """ บันทึกข้อมูลการตรวจจับลงในฐานข้อมูล """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    