from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid
import random
from typing import List, Optional
from storage3.exceptions import StorageApiError

from app.core.security import get_current_user
from app.dependencies.db import get_db
from app.models.user_model import User, Otp
from app.schemas.user_schema import Login, ForgotPassword, VerifyOTP, ResetPassword
from app.core.security import hash_password, verify_password, create_token
from app.utils.email import send_otp_email
from app.core.supabase import supabase

router = APIRouter(prefix="/auth", tags=["Auth"])


# ==========================
# SIGNUP
# ==========================
@router.post("/signup")
def signup(
    name: str = Form(...),
    profession: List[str] = Form(...),
    countryCode: str = Form(...),
    city: str = Form(...),
    role: str = Form(...),
    address: str = Form(...),
    phoneNumber: str = Form(...),
    phoneNumber1: Optional[str] = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    bio:Optional[str] = Form(None),
    confirm_password: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):

    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    file_path = None

    # ==========================
    # Upload Photo to Supabase
    # ==========================
    if photo and photo.filename:

        file_extension = photo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"

        file_bytes = photo.file.read()

        try:
            supabase.storage.from_("user-photos").upload(
                path=f"photos/{filename}",
                file=file_bytes,
                file_options={"content-type": photo.content_type}
            )

            public_url = supabase.storage.from_("user-photos").get_public_url(filename)

            file_path = public_url

        except StorageApiError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Photo upload failed: {str(exc)}"
            )

    hashed_password = hash_password(password)

    new_user = User(
        name=name,
        profession=profession,
        countryCode=countryCode,
        city=city,
        role=role,
        address=address,
        phone=phoneNumber,
        alternate_phone=phoneNumber1,
        email=email,
        bio=bio,
        password=hashed_password,
        photo=file_path
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_token({
        "user_id": new_user.id,
        "email": new_user.email
    })

    return {
        "message": "Signup successful",
        "user_id": new_user.id,
        "token": token
    }

# ==========================
# LOGIN
# ==========================
@router.post("/login")
def login(user: Login, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == user.email,User.role == user.role).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_token({
        "user_id": db_user.id,
        "email": db_user.email
    })

    return {
        "message": "Login successful",
        "token": token
    }


# ==========================
# LOGOUT
# ==========================
@router.post("/logout")
def logout(current_user = Depends(get_current_user)):
    return {
        "message": "Logout successful"
    }


# ==========================
# FORGOT PASSWORD
# ==========================
@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # delete previous OTPs
    db.query(Otp).filter(Otp.userId == user.id).delete()
    db.commit()

    otp_code = str(random.randint(1000, 9999))

    otp = Otp(
        otp=otp_code,
        userId=user.id,
        isVerify=False
    )

    db.add(otp)
    db.commit()

    send_otp_email(user.email, otp_code)

    return {
        "message": "OTP sent to your email"
    }


# ==========================
# VERIFY OTP
# ==========================
@router.post("/verify-otp")
def verify_otp(data: VerifyOTP, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = db.query(Otp).filter(
        Otp.userId == user.id,
        Otp.otp == data.otp,
        Otp.isVerify == False
    ).first()

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    otp.isVerify = True
    db.commit()

    return {
        "message": "OTP verified successfully"
    }


# ==========================
# RESET PASSWORD
# ==========================
@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = db.query(Otp).filter(
        Otp.userId == user.id,
        Otp.isVerify == True
    ).first()

    if not otp:
        raise HTTPException(status_code=400, detail="OTP not verified")

    hashed_password = hash_password(data.new_password)

    user.password = hashed_password

    db.delete(otp)

    db.commit()

    return {
        "message": "Password reset successful"
    }

