
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional


# -------------------------
# SIGNUP SCHEMA
# -------------------------
class Signup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    profession: List[str]
    countryCode: str
    role: str
    city: str
    address: str
    phoneNumber: str = Field(..., min_length=10, max_length=15)
    phoneNumber1: Optional[str] = None
    bio: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    # password match validation
    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# -------------------------
# LOGIN SCHEMA
# -------------------------
class Login(BaseModel):
    email: EmailStr
    role: str
    password: str


# -------------------------
# FORGOT PASSWORD
# -------------------------
class ForgotPassword(BaseModel):
    email: EmailStr


# -------------------------
# VERIFY OTP
# -------------------------
class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=4)


# -------------------------
# RESET PASSWORD
# -------------------------
class ResetPassword(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6)

