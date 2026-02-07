import os
from functools import lru_cache
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# =========================
# Firebase Config
# =========================

USE_FIREBASE = os.getenv("USE_FIREBASE", "false").lower() == "true"

@lru_cache()
def initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK
    Returns True if initialized, False otherwise
    """
    if not USE_FIREBASE:
        print("🚫 Firebase Admin SDK disabled (USE_FIREBASE=false)")
        return False

    try:
        cred_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT_KEY",
            "/app/serviceAccountKey.json"
        )

        print(f"🔍 Looking for Firebase key at: {os.path.abspath(cred_path)}")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"❌ Service account key not found: {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        print("✅ Firebase Admin SDK initialized successfully")
        return True

    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


FIREBASE_ENABLED = initialize_firebase()

# =========================
# Security
# =========================

security = HTTPBearer(auto_error=False)

# =========================
# Firebase Token Verify - NO TIME CHECK
# =========================

async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify Firebase ID Token (signature only, no time validation)
    """
    print(f"🔍 FIREBASE_ENABLED: {FIREBASE_ENABLED}")
    
    if not FIREBASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is disabled"
        )

    if not credentials:
        print("❌ No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    token = credentials.credentials
    print(f"🔑 Token received (first 50 chars): {token[:50]}...")

    try:
   
        import jwt
        
 
        app = firebase_admin.get_app()
        project_id = app.project_id
        
       
        unverified_claims = jwt.decode(token, options={"verify_signature": False})
        
        
        uid = (
            unverified_claims.get('uid') or 
            unverified_claims.get('user_id') or 
            unverified_claims.get('sub')
        )
        
        email = unverified_claims.get('email')
        name = unverified_claims.get('name')
        picture = unverified_claims.get('picture')

        print(f"🔍 Token claims (unverified):")
        print(f"   UID: {uid}")
        print(f"   Email: {email}")
        print(f"   Name: {name}")
        print(f"   Issued at: {unverified_claims.get('iat')}")
        print(f"   Expires at: {unverified_claims.get('exp')}")
        
       
        if not uid:
            print(f"❌ Missing UID. Available claims: {list(unverified_claims.keys())}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID"
            )
        
     
        aud = unverified_claims.get('aud')
        if aud != project_id:
            print(f"❌ Invalid audience. Expected: {project_id}, Got: {aud}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience"
            )
        
        
        try:
            decoded_token = auth.verify_id_token(token, check_revoked=False)
            print(f"✅ Signature verified")
        except Exception as e:
            error_str = str(e).lower()
            
            if "too early" in error_str or "expired" in error_str:
                print(f"⚠️  Time validation skipped: {e}")
                decoded_token = unverified_claims
            else:
                
                print(f"❌ Signature verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token signature: {str(e)}"
                )
        
        print(f"✅ Token verified successfully (time check skipped)!")
        print(f"   Email: {email}")
        print(f"   UID: {uid}")

        return {
            "firebase_uid": uid,
            "email": email,
            "name": name,
            "picture": picture,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}")
        print(f"   Details: {str(e)}")
        import traceback
        traceback.print_exc()
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
    """
    if not FIREBASE_ENABLED or not credentials:
        return None

    try:
        return await verify_firebase_token(credentials)
    except Exception:
        return None