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

