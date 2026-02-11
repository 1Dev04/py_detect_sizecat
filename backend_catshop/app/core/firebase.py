import os
import firebase_admin
from firebase_admin import credentials


def init_firebase() -> None:
    # กัน init ซ้ำ
    if firebase_admin._apps:
        return

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")

    if not all([project_id, client_email, private_key]):
        raise RuntimeError("Missing Firebase ENV variables")

    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": project_id,
        "client_email": client_email,
        "private_key": private_key.replace("\\n", "\n").strip('"'),
        "token_uri": "https://oauth2.googleapis.com/token",
    })

    firebase_admin.initialize_app(cred)