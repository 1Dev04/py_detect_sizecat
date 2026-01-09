from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.db.session import get_db
from backend_catshop.app.models.dbcat import Cat

router = APIRouter (
    prefix="/api/system",
    tags=["System"]
)

class CatBase(BaseModel):
    name: str
    breed: str | None = None
    age: int | None = None
    weight: float
    size_category: str
    chest_cm: float
    neck_cm: float | None = None
    body_length_cm: float | None = None
    confidence: float
    image_url: str
    thumbnail_url: str | None = None


class CatCreate(CatBase):
    pass


class CatUpdate(BaseModel):
    name: str | None = None
    breed: str | None = None
    age: int | None = None
    weight: float | None = None
    size_category: str | None = None
    chest_cm: float | None = None
    neck_cm: float | None = None
    body_length_cm: float | None = None
    confidence: float | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None


class CatResponse(CatBase):
    id: int
    detected_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True



# API 

@router.post("/cat", response_model=CatResponse)
def create_cat(cat: CatCreate, db: Session = Depends(get_db)):
    new_cat = Cat(
        **cat.dict(),
        detected_at= datetime.utcnow()
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)

    return new_cat

@router.get("/cats", response_model=List[CatResponse])
def get_all_cats(db: Session = Depends(get_db)):
    return db.query(Cat).order_by(Cat.detected_at.desc()).all()

@router.get("/cats/{cat_id}", response_model=CatResponse)
def get_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat: 
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat

@router.put("/cats/{cat_id}", response_model=CatResponse)
def update_cat(
    cat_id: int,
    payload: CatUpdate,
    db: Session = Depends(get_db)
):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(cat, key, value)

    cat.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/cats/{cat_id}")
def delete_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    db.delete(cat)
    db.commit()
    return {"message": "Cat deleted successfully"}