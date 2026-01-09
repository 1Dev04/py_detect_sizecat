from ultralytics import YOLO
from pathlib import Path
import cv2

# ===== PATH CONFIG =====
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_IMG_DIR = BASE_DIR / "ml/dataset/images/raw"
LABEL_DIR = BASE_DIR / "ml/dataset/labels/train"

MODEL_PATH = BASE_DIR / "yolov8m.pt"  # base model (COCO)

LABEL_DIR.mkdir(parents=True, exist_ok=True)

# COCO class id for "cat"
CAT_CLASS_ID = 15

print("🐱 Loading YOLOv8 model...")
model = YOLO(str(MODEL_PATH))

images = list(RAW_IMG_DIR.glob("*.jpg"))

print(f"📸 Found {len(images)} images")

for img_path in images:
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]

    results = model(img, conf=0.4, iou=0.5, verbose=False)
    r = results[0]

    label_lines = []

    if r.boxes is not None:
        for box in r.boxes:
            cls_id = int(box.cls[0])

            # 🔥 เอาเฉพาะแมว
            if cls_id != CAT_CLASS_ID:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # YOLO format (normalized)
            x_center = ((x1 + x2) / 2) / w
            y_center = ((y1 + y2) / 2) / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h

            label_lines.append(
                f"0 {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}"
            )

    # save label
    label_path = LABEL_DIR / f"{img_path.stem}.txt"

    if label_lines:
        with open(label_path, "w") as f:
            f.write("\n".join(label_lines))
        print(f"✅ Labeled: {img_path.name}")
    else:
        print(f"⚠️ No cat detected: {img_path.name}")

print("\n🎉 Auto-label completed (cats only)")