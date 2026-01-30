from sqlalchemy import Column, Integer, String, Numeric, Text, TIMESTAMP, JSON, CheckConstraint, Index
from sqlalchemy.sql import func
from catshop_system.backend_catshop.app.db.database import Base

class Cat(Base):
    """
    Model สำหรับเก็บข้อมูลแมวที่ detect จาก AI
    """
    __tablename__ = "cats"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Cat Info
    cat_color = Column(String(100), nullable=True, comment="สีแมว")
    breed = Column(String(100), nullable=True, comment="สายพันธุ์")
    age = Column(Integer, CheckConstraint('age >= 0'), nullable=True, comment="อายุ")
    
    # Weight & Size
    weight = Column(
        Numeric(5, 2), 
        CheckConstraint('weight > 0'), 
        nullable=False,
        comment="น้ำหนัก (kg)"
    )
    size_category = Column(
        String(5),
        CheckConstraint("size_category IN ('XS','S','M','L','XL')"),
        nullable=False,
        comment="ขนาด"
    )
    
    # Measurements
    chest_cm = Column(Numeric(6, 2), nullable=True, comment="รอบอก (cm)")
    neck_cm = Column(Numeric(6, 2), nullable=True, comment="รอบคอ (cm)")
    body_length_cm = Column(Numeric(6, 2), nullable=True, comment="ความยาวตัว (cm)")
    
    # AI Detection Info
    confidence = Column(
        Numeric(5, 4),
        CheckConstraint('confidence BETWEEN 0 AND 1'),
        nullable=True,
        comment="ความมั่นใจจาก AI (0-1)"
    )
    bounding_box = Column(JSON, nullable=True, comment="พิกัด bounding box [x1, y1, x2, y2]")
    
    # Images
    image_url = Column(Text, nullable=False, comment="Cloudinary URL")
    thumbnail_url = Column(Text, nullable=True, comment="รูป thumbnail")
    
    # Timestamps
    detected_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="วันที่ detect"
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_cats_size_category', 'size_category'),
        Index('idx_cats_detected_at', 'detected_at'),
        Index('idx_cats_cat_color', 'cat_color'),
    )
    
    def __repr__(self):
        return f"<Cat(id={self.id}, color={self.cat_color}, breed={self.breed}, size={self.size_category})>"