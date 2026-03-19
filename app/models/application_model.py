from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base



class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(Integer, ForeignKey("users.id"))
    provider_id = Column(Integer, ForeignKey("users.id"))

    message = Column(Text)
    photo = Column(String, nullable=True)

    status = Column(String, default="pending") 

    created_at = Column(DateTime, default=func.now())

    # optional relationships
    client = relationship("User", foreign_keys=[client_id])
    provider = relationship("User", foreign_keys=[provider_id])