import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
from pathlib import Path
import os
import requests

# โหลด env
load_dotenv()


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ===== CONFIG =====
CLOUDINARY_FOLDER = "Fetch_Img_SizeCat"
SAVE_DIR = Path("ml/dataset/images/raw")
MAX_IMAGES = 1000

SAVE_DIR.mkdir(parents=True, exist_ok=True)

print("🔗 Connecting to Cloudinary...")
print(f"📂 Folder: {CLOUDINARY_FOLDER}")
print(f"💾 Save to: {SAVE_DIR.resolve()}")

# ===== FETCH IMAGES =====
resources = []
next_cursor = None

while True:
    result = cloudinary.api.resources(
        type="upload",
        prefix=CLOUDINARY_FOLDER,
        resource_type="image",
        max_results=100,
        next_cursor=next_cursor,
    )

    resources.extend(result["resources"])
    next_cursor = result.get("next_cursor")

    if not next_cursor or len(resources) >= MAX_IMAGES:
        break

resources = resources[:MAX_IMAGES]

print(f"📥 Found {len(resources)} images")

# ===== DOWNLOAD =====
for idx, res in enumerate(resources, start=1):
    url = res["secure_url"]
    filename = f"{res['public_id'].replace('/', '_')}.jpg"
    save_path = SAVE_DIR / filename

    if save_path.exists():
        continue

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(r.content)

    print(f"[{idx}/{len(resources)}] ✅ Downloaded {filename}")

print("\n🎉 Done! Images saved to raw folder.")