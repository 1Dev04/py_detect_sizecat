import os
import firebase_admin
from firebase_admin import credentials


def init_firebase() -> bool:
    """
    Init Firebase Admin SDK
    Priority:
    1) Environment variables (Render / Production)
    2) serviceAccount.json file (Local dev)
    3) Skip if not configured
    """

    # ปิด Firebase ทั้งระบบได้ด้วย env เดียว
    if os.getenv("USE_FIREBASE", "false").lower() != "true":
        print("🚫 Firebase disabled (USE_FIREBASE=false)")
        return False

    # กัน init ซ้ำ
    if firebase_admin._apps:
        return True

    # ---------- 1) ENV ----------
    env_keys = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_PRIVATE_KEY",
    ]

    if all(os.getenv(k) for k in env_keys):
        try:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": os.environ["FIREBASE_PROJECT_ID"],
                "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
                "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
            })
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase initialized via ENV")
            return True
        except Exception as e:
            print(f"❌ Firebase ENV init failed: {e}")

    # ---------- 2) FILE ----------
    service_account_path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        "app/serviceAccount.json"
    )

    if os.path.exists(service_account_path):
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print(f"🔥 Firebase initialized via FILE ({service_account_path})")
            return True
        except Exception as e:
            print(f"❌ Firebase FILE init failed: {e}")

    # ---------- 3) SKIP ----------
    print("⚠️ Firebase not configured, skipping init")
    return False
