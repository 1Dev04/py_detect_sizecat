from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.dbcat import Cat
from app.schemas.cat import CatCreate, CatUpdate, CatResponse
from app.auth.dependencies import verify_firebase_token
from app.utils.response import success_response, error_response

router = APIRouter(
    prefix="/api/system",
    tags=["System - Cat CRUD"]
)

# ============================================
# CREATE - สร้างข้อมูลแมว
# ============================================
@router.post("/cats", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_cat(
    cat: CatCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Create a new cat record
    
    **Authentication:** Firebase ID Token required
    
    **Body:**
    - name: Cat name
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
        new_cat = Cat(
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
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cat: {str(e)}"
        )

# ============================================
# READ - อ่านข้อมูลแมวทั้งหมด
# ============================================
@router.get("/cats", response_model=dict)
def get_all_cats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Get all cats with pagination
    
    **Authentication:** Firebase ID Token required
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    """
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
            message=f"Retrieved {len(cats)} cats"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cats: {str(e)}"
        )

# ============================================
# READ - อ่านข้อมูลแมวตัวเดียว
# ============================================
@router.get("/cats/{cat_id}", response_model=dict)
def get_cat(
    cat_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Get a specific cat by ID
    
    **Authentication:** Firebase ID Token required
    
    **Path Parameters:**
    - cat_id: Cat ID
    """
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with ID {cat_id} not found"
        )
    
    return success_response(
        data=CatResponse.from_orm(cat).model_dump(),
        message="Cat retrieved successfully"
    )

# ============================================
# UPDATE - อัปเดตข้อมูลแมว
# ============================================
@router.put("/cats/{cat_id}", response_model=dict)
def update_cat(
    cat_id: int,
    payload: CatUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Update a cat record
    
    **Authentication:** Firebase ID Token required
    
    **Path Parameters:**
    - cat_id: Cat ID
    
    **Body:** All fields are optional
    """
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with ID {cat_id} not found"
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
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cat: {str(e)}"
        )

# ============================================
# DELETE - ลบข้อมูลแมว
# ============================================
@router.delete("/cats/{cat_id}", response_model=dict)
def delete_cat(
    cat_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Delete a cat record
    
    **Authentication:** Firebase ID Token required
    
    **Path Parameters:**
    - cat_id: Cat ID
    """
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with ID {cat_id} not found"
        )
    
    try:
        db.delete(cat)
        db.commit()
        
        return success_response(
            data={"id": cat_id},
            message="Cat deleted successfully"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cat: {str(e)}"
        )

# ============================================
# SEARCH - ค้นหาแมวตามเกณฑ์
# ============================================
@router.get("/cats/search", response_model=dict)
def search_cats(
    breed: str = None,
    size_category: str = None,
    min_weight: float = None,
    max_weight: float = None,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    """
    Search cats by criteria
    
    **Authentication:** Firebase ID Token required
    
    **Query Parameters:**
    - breed: Filter by breed (optional)
    - size_category: Filter by size (XS, S, M, L, XL) (optional)
    - min_weight: Minimum weight in kg (optional)
    - max_weight: Maximum weight in kg (optional)
    """
    query = db.query(Cat)
    
    if breed:
        query = query.filter(Cat.breed.ilike(f"%{breed}%"))
    
    if size_category:
        query = query.filter(Cat.size_category == size_category)
    
    if min_weight:
        query = query.filter(Cat.weight >= min_weight)
    
    if max_weight:
        query = query.filter(Cat.weight <= max_weight)
    
    cats = query.order_by(Cat.detected_at.desc()).all()
    
    return success_response(
        data={
            "cats": [CatResponse.from_orm(cat).model_dump() for cat in cats],
            "total": len(cats),
            "filters": {
                "breed": breed,
                "size_category": size_category,
                "min_weight": min_weight,
                "max_weight": max_weight
            }
        },
        message=f"Found {len(cats)} cats matching criteria"
    )