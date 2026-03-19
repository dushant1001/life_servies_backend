from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Document(Base):

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    document_type = Column(String(100))   # aadhar, pan, license
    document_number = Column(String(100), nullable=True)
    file_url = Column(String(255))        # Supabase URL
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    userId = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="documents")
