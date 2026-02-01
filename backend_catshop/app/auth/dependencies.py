from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
import os
from functools import lru_cache

# =========================
# Firebase Config
# =========================

USE_FIREBASE = os.getenv("USE_FIREBASE", "false").lower() == "true"

@lru_cache()
def initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK (optional)
    Returns True if initialized, False otherwise
    """
    if not USE_FIREBASE:
        print("🚫 Firebase Admin SDK disabled (USE_FIREBASE=false)")
        return False

    try:
        cred_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT_KEY",
            "serviceAccountKey.json"
        )

        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Service account key not found: {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        print("✅ Firebase Admin SDK initialized")
        return True

    except Exception as e:
        print(f"⚠️ Firebase initialization error: {e}")
        return False


FIREBASE_ENABLED = initialize_firebase()

# =========================
# Security
# =========================

security = HTTPBearer(auto_error=False)

# =========================
# Firebase Token Verify
# =========================

async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify Firebase ID Token (required auth)
    """
    if not FIREBASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is disabled"
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)

        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
        }

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

# =========================
# Optional Firebase Auth
# =========================

async def optional_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict | None:
    """
    Optional Firebase token verification
    - Returns None if Firebase disabled
    - Returns None if no token
    """
    if not FIREBASE_ENABLED or not credentials:
        return None

    try:
        return await verify_firebase_token(credentials)
    except Exception:
        return None
