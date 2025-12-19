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
    'port': os.getenv('DB_PORT'),
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
     """ ตรวจจับแมวและวัดขนาด"""
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
    
    try: 
        cursor = connection.cursor()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        query = """
                  
        """
        values = (
            cat_data.get('name', 'Unknown Cat'),
            'Cat',
            cat_data.get('description', 'Detected cat'),
            cat_data.get('size_category', 'Unknown'),
            cat_data.get('price', 0.00),
            cat_data.get('width_cm', 0),
            cat_data.get('height_cm', 0),
            cat_data.get('confidence', 0),
            str(cat_data.get('bbox', [])),
            image_base64[:65000],  # จำกัดขนาด (หรือเก็บเป็นไฟล์)
            datetime.now()
        )

        cursor.execute(query, values)
        connection.commit()

        cat_id = cursor.lastrowid
        return cat_id
        
    except Error as e:
        print(f"Error saving to database: {e}")
        raise e
    finally: 
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/")
def read_root():
    return {"message": "Cat Detection API is running.", "version" : "1.0"}

@app.post("/api/detectsize/cat")
async def detect_cat(file: UploadFile = File(...)):
    """ API Endpoint สำหรับตรวจจจับและวัดขนาดแมว"""
    try: 
        contents = await file.read()

        detections = detect_cat_size(contents)
        if not detections:
            return {
                "success": False,
                "message": "No cat detected in the image.",
                "data": None
            }
        
        main_cat = max(detections, key=lambda x: x['confidence'])

        cat_id = save_to_database(main_cat, contents)

        response_data = {}