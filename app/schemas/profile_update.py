from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UpdateProfile(BaseModel):
    name: Optional[str] = None
    profession: Optional[List[str]] = None
    countryCode: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    phoneNumber: Optional[str] = None
    alternate_phone: Optional[str] = None
    phoneNumber1: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
