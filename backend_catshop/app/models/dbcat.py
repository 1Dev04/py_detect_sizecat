from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base import Base
from datetime import datetime

class Cat(Base):
    __tablename__ = "cats"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    breed = Column(String)
    age = Column(Integer)

    weight = Column(Float, nullable=False)
    size_category = Column(String, nullable=False)

    chest_cm = Column(Float, nullable=False)
    neck_cm = Column(Float)
    body_length_cm = Column(Float)

    confidence = Column(Float, nullable=False)

    image_url = Column(String, nullable=False)
    thumbnail_url = Column(String)

    detected_at = Column(DateTime, default=datetime.utcnow)
