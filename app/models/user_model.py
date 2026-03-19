import json

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)


    name = Column(String(100))
    role = Column(String(50), nullable=False)
    _profession = Column("profession", Text, nullable=False)

    countryCode = Column("country", String(100))
    city = Column(String(100), nullable=False)

    address = Column(Text)

    phone = Column(String(20))
    alternate_phone = Column(String(20))

    email = Column(String(150), unique=True)

    password = Column(String(255))

    photo = Column(String(255),nullable=True)
    bio = Column(String(255))

    otps = relationship("Otp", back_populates="user")
    documents = relationship("Document", back_populates="user")

    @property
    def profession(self):
        if not self._profession:
            return []

        try:
            value = json.loads(self._profession)
        except json.JSONDecodeError:
            return [item.strip() for item in self._profession.split(",") if item.strip()]

        if isinstance(value, list):
            return value

        return [str(value)]

    @profession.setter
    def profession(self, value):
        if value is None:
            self._profession = "[]"
            return

        if isinstance(value, list):
            self._profession = json.dumps(value)
            return

        if isinstance(value, str):
            stripped_value = value.strip()
            if stripped_value.startswith("["):
                try:
                    parsed_value = json.loads(stripped_value)
                except json.JSONDecodeError:
                    self._profession = json.dumps([value])
                    return

                self._profession = json.dumps(parsed_value if isinstance(parsed_value, list) else [parsed_value])
                return

        self._profession = json.dumps([value])


class Otp(Base):

    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    isVerify = Column(Boolean, default=False)
    otp = Column(String(10))
    userId = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="otps")
