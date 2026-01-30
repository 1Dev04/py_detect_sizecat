from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
import os
from functools import lru_cache

# Initialize Firebase Admin SDK (call one time)
@lru_cache()
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try: 
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "serviceAccountKey.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
    except Exception as e:
        print(f"⚠️  Firebase initialization error: {e}")


# initialize เมื่อ import module 
initialize_firebase()

# Security scheme
security = HTTPBearer()

async def verify_firebase_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify Firebase ID Token

    Returns: 
        dict: {
            "uid": "user_firebase_uid",
            "email": "user123@example.com"
            "name": "User Name"
        }
    """
    token = credentials.credentials

    try: 
        # Verify Token by Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)

        return {
            "uid": decoded_token["uid"],
            "email": decoded_token["email"],
            "name": decoded_token["name"],
            "picture": decoded_token["picture"],
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
# endpoint not auth (optional)
async def optional_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict | None: 
    """
        Optional Firebase token verification
        Returns None if no token provided
    """
    if not credentials:
        return None
    
    try: 
        return await verify_firebase_token(credentials)
    except: 
        return None
    