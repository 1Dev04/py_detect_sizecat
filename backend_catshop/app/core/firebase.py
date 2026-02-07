import os
import firebase_admin
from firebase_admin import credentials

def init_firebase():
    if os.getenv("USE_FIREBASE", "false").lower() != "true":
        print("🚫 Firebase disabled, skipping init")
        return False

    if firebase_admin._apps:
        return True

    required_envs = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_PRIVATE_KEY",
    ]

    missing = [k for k in required_envs if not os.getenv(k)]
    if missing:
        print(f"⚠️ Firebase enabled but missing envs: {', '.join(missing)}")
        print("👉 Skipping Firebase init")
        return False

    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": os.environ["FIREBASE_PROJECT_ID"],
        "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
        "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
    })

    firebase_admin.initialize_app(cred)
    print("🔥 Firebase initialized")
    return True

   
