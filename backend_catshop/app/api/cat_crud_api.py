# Crud Cat api 

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.db.database import get_db
from app.models.dbcat import Cat
from app.schemas.cat import CatCreate, CatUpdate, CatResponse
from app.auth.dependencies import verify_firebase_token
from app.utils.response import success_response, error_response

router = APIRouter(
    prefix="/api",
    tags=["System - Cat CRUD"]
)

# ============================================
# CREATE - สร้างข้อมูลแมว
# ============================================
@router.post("/system/cats", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_cat(
    cat: CatCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Create a new cat record
    
    **Authentication:** Firebase ID Token required
    
    **Body:**
    - firebase_uid: Firebase UID (from auth token)
    - name: Cat name/color
    - breed: Cat breed (optional)
    - age: Cat age in years (optional)
    - weight: Cat weight in kg
    - size_category: XS, S, M, L, XL
    - chest_cm: Chest circumference in cm
    - neck_cm: Neck circumference in cm (optional)
    - body_length_cm: Body length in cm (optional)
    - confidence: Prediction confidence (0-1)
    - image_url: Full image URL
    - thumbnail_url: Thumbnail URL (optional)
    """
    try:
        # 🔐 ดึง firebase_uid จาก token
        firebase_uid = user.get("uid")
        
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )
        
        # สร้าง Cat object พร้อม firebase_uid
        new_cat = Cat(
            firebase_uid=firebase_uid,
            **cat.model_dump(),
            detected_at=datetime.utcnow()
        )
        
        db.add(new_cat)
        db.commit()
        db.refresh(new_cat)
        
        return success_response(
            data=CatResponse.from_orm(new_cat).model_dump(),
            message="Cat created successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cat: {str(e)}"
        )

# ============================================
# READ - อ่านข้อมูลแมวทั้งหมดของ User
# ============================================
@router.get("/system/cats", response_model=dict)
def get_user_cats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Get all cats owned by the authenticated user
    
    **Authentication:** Firebase ID Token required
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    """
    try:
        firebase_uid = user.get("uid")
        
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )
        
        # 🔥 Query เฉพาะแมวของ user คนนี้
        cats = db.query(Cat)\
                 .filter(Cat.firebase_uid == firebase_uid)\
                 .order_by(Cat.detected_at.desc())\
                 .offset(skip)\
                 .limit(limit)\
                 .all()
        
        total = db.query(Cat).filter(Cat.firebase_uid == firebase_uid).count()
        
        return success_response(
            data={
                "cats": [CatResponse.from_orm(cat).model_dump() for cat in cats],
                "total": total,
                "skip": skip,
                "limit": limit
            },
            message=f"Retrieved {len(cats)} cats"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cats: {str(e)}"
        )

# ============================================
# READ - อ่านข้อมูลแมวตัวเดียว
# ============================================
@router.get("/system/cats/{cat_id}", response_model=dict)
def get_cat(
    cat_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Get a specific cat by ID (must be owned by user)
    
    **Authentication:** Firebase ID Token required
    
    **Path Parameters:**
    - cat_id: Cat ID
    """
    firebase_uid = user.get("uid")
    
    # 🔒 ตรวจสอบว่าเป็นแมวของ user คนนี้
    cat = db.query(Cat)\
            .filter(Cat.id == cat_id)\
            .filter(Cat.firebase_uid == firebase_uid)\
            .first()
    
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with ID {cat_id} not found or not owned by you"
        )
    
    return success_response(
        data=CatResponse.from_orm(cat).model_dump(),
        message="Cat retrieved successfully"
    )

# ============================================
# UPDATE - อัปเดตข้อมูลแมว
# ============================================
@router.put("/system/cats/{cat_id}", response_model=dict)
def update_cat(
    cat_id: int,
    payload: CatUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Update a cat record (must be owned by user)
    
    **Authentication:** Firebase ID Token required
    
    **Path Parameters:**
    - cat_id: Cat ID
    
    **Body:** All fields are optional
    - name, breed, age, weight, etc.
    """
    firebase_uid = user.get("uid")
    
    # 🔒 ตรวจสอบว่าเป็นแมวของ user คนนี้
    cat = db.query(Cat)\
            .filter(Cat.id == cat_id)\
            .filter(Cat.firebase_uid == firebase_uid)\
            .first()
    
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with ID {cat_id} not found or not owned by you"
        )
    
    try:
        # Update only provided fields
        update_data = payload.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(cat, key, value)
        
        cat.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(cat)
        
        return success_response(
            data=CatResponse.from_orm(cat).model_dump(),
            message="Cat updated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cat: {str(e)}"
        )

# ============================================
# DELETE - ลบข้อมูลแมว
# ============================================
@router.delete("/system/cats/{cat_id}", response_model=dict)
def delete_cat(
    cat_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Delete a cat record (must be owned by user)
    
    **Authentication:** Firebase ID Token required
    
    **Path Parameters:**
    - cat_id: Cat ID
    """
    firebase_uid = user.get("uid")
    
    # 🔒 ตรวจสอบว่าเป็นแมวของ user คนนี้
    cat = db.query(Cat)\
            .filter(Cat.id == cat_id)\
            .filter(Cat.firebase_uid == firebase_uid)\
            .first()
    
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with ID {cat_id} not found or not owned by you"
        )
    
    try:
        db.delete(cat)
        db.commit()
        
        return success_response(
            data={"id": cat_id, "deleted": True},
            message="Cat deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cat: {str(e)}"
        )

# ============================================
# SEARCH - ค้นหาแมวตามเกณฑ์ (ของ User คนนั้น)
# ============================================
@router.get("/system/cats/search", response_model=dict)
def search_cats(
    breed: Optional[str] = None,
    size_category: Optional[str] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Search cats by criteria (only user's cats)
    
    **Authentication:** Firebase ID Token required
    
    **Query Parameters:**
    - breed: Filter by breed (optional)
    - size_category: Filter by size (XS, S, M, L, XL) (optional)
    - min_weight: Minimum weight in kg (optional)
    - max_weight: Maximum weight in kg (optional)
    - skip: Pagination skip (default: 0)
    - limit: Pagination limit (default: 100)
    """
    firebase_uid = user.get("uid")
    
    # 🔥 เริ่มจาก query แมวของ user คนนี้
    query = db.query(Cat).filter(Cat.firebase_uid == firebase_uid)
    
    if breed:
        query = query.filter(Cat.breed.ilike(f"%{breed}%"))
    
    if size_category:
        query = query.filter(Cat.size_category == size_category)
    
    if min_weight:
        query = query.filter(Cat.weight >= min_weight)
    
    if max_weight:
        query = query.filter(Cat.weight <= max_weight)
    
    total = query.count()
    cats = query.order_by(Cat.detected_at.desc()).offset(skip).limit(limit).all()
    
    return success_response(
        data={
            "cats": [CatResponse.from_orm(cat).model_dump() for cat in cats],
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters": {
                "breed": breed,
                "size_category": size_category,
                "min_weight": min_weight,
                "max_weight": max_weight
            }
        },
        message=f"Found {len(cats)} cats matching criteria"
    )

# ============================================
# ADMIN - ดูแมวทั้งหมดในระบบ (Admin only)
# ============================================
@router.get("/system/admin/cats/all", response_model=dict)
def get_all_cats_admin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Get ALL cats in system (Admin only)
    
    **Authentication:** Firebase ID Token required + Admin role
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    """
    # TODO: เพิ่มการตรวจสอบ admin role
    # if not user.get("is_admin"):
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        cats = db.query(Cat)\
                 .order_by(Cat.detected_at.desc())\
                 .offset(skip)\
                 .limit(limit)\
                 .all()
        
        total = db.query(Cat).count()
        
        return success_response(
            data={
                "cats": [CatResponse.from_orm(cat).model_dump() for cat in cats],
                "total": total,
                "skip": skip,
                "limit": limit
            },
            message=f"Retrieved {len(cats)} cats (admin view)"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cats: {str(e)}"
        )