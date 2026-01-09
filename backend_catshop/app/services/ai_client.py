import requests

def detect_cat(image_url: str):
    res = requests.post(
        "http://ai-service:9000/detect",
        json={"image_url": image_url}
    )
    return res.json()