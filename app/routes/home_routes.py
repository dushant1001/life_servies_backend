from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.dependencies.db import get_db
from app.models.user_model import User

router = APIRouter(prefix="/home", tags=["Home"])


# ==========================
# GET ALL PROFILES
# ==========================
@router.get("/get")
def get_all_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # -------- ROLE CHECK --------
    if current_user.role.lower() == "client":
        target_role = "service_provider"

    elif current_user.role.lower() == "service_provider":
        target_role = "client"

    else:
        raise HTTPException(status_code=400, detail="Invalid role")

    users = db.query(User).filter(User.role == target_role).all()

    return {
        "count": len(users),
        "profiles": [
            {
                "id": user.id,
                "name": user.name,
                "profession": user.profession,
                "bio": user.bio,
                "photo": user.photo,
            }
            for user in users
        ],
    }

# ==========================
# GET PROFILE BY ID
# ==========================
@router.get("/get_profile/{user_id}")
def get_profile_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profession": user.profession,
        "role": user.role,
        "city": user.city,
        "address": user.address,
        "phone": user.phone,
        "alternate_phone": user.alternate_phone,
        "bio": user.bio,
        "photo": user.photo,
    }