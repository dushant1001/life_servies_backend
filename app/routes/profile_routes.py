from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.dependencies.db import get_db
from app.models.user_model import User
from app.schemas.profile_update import UpdateProfile

router = APIRouter(prefix="/profile", tags=["Profile"])


# ==========================
# GET PROFILE
# ==========================
@router.get("/get")
def get_profile(current_user: User = Depends(get_current_user)):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "profession": current_user.profession,
        "role": current_user.role,
        "city": current_user.city,
        "address": current_user.address,
        "phone": current_user.phone,
        "alternate_phone": current_user.alternate_phone,
        "bio": current_user.bio,
        "photo": current_user.photo,
    }


# ==========================
# UPDATE PROFILE
# ==========================
@router.put("/update")
def update_profile(
    data: UpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # -------- EMAIL UPDATE --------
    if data.email is not None:
        existing_user = db.query(User).filter(User.email == data.email).first()

        if existing_user and existing_user.id != user.id:
            raise HTTPException(status_code=400, detail="Email already exists")

        user.email = data.email

    # -------- NORMAL FIELDS --------
    if data.name is not None:
        user.name = data.name

    if data.profession is not None:
        user.profession = data.profession

    if data.countryCode is not None:
        user.countryCode = data.countryCode


    if data.city is not None:
        user.city = data.city

    if data.address is not None:
        user.address = data.address

    phone_value = data.phoneNumber if data.phoneNumber is not None else data.phone
    if phone_value is not None:
        user.phone = phone_value

    alternate_phone_value = (
        data.phoneNumber1 if data.phoneNumber1 is not None else data.alternate_phone
    )
    if alternate_phone_value is not None:
        user.alternate_phone = alternate_phone_value

    if data.bio is not None:
        user.bio = data.bio

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "profession": user.profession,
            "city": user.city,
            "bio": user.bio,
            "photo": user.photo,
        },
    }
