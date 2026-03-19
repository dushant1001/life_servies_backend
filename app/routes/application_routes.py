import os
import uuid
import json
import shutil
from typing import List,Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.core.security import get_current_user
from app.models.application_model import Application
from app.models.user_model import User
from app.core.supabase import supabase
from storage3.exceptions import StorageApiError

router = APIRouter(prefix="/application", tags=["Application"])

# ==========================
# CREATE UPLOAD FOLDER
# ==========================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==========================
# RESPONSE FORMATTER
# ==========================
def format_app_response(app_obj, request: Request = None):
    photo_paths = json.loads(app_obj.photo) if app_obj.photo else []

    if request:
        base_url = str(request.base_url)
        photo_paths = [f"{base_url}uploads/{name}" for name in photo_paths]

    return {
        "id": app_obj.id,
        "client_id": app_obj.client_id,
        "provider_id": app_obj.provider_id,
        "message": app_obj.message,
        "photo": photo_paths,
        "status": app_obj.status,
        "created_at": app_obj.created_at
    }

# ==========================
# SEND APPLICATION (MULTIPLE FILES)
# ==========================
@router.post("/send/{provider_id}")
async def send_application(
    provider_id: int,
    request: Request,
    message: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. ROLE CHECK
    if current_user.role.lower() != "client":
        raise HTTPException(status_code=403, detail="Only clients can send applications")

    # 2. PROVIDER CHECK
    provider = db.query(User).filter(User.id == provider_id).first()
    if not provider or provider.role.lower() != "service_provider":
        raise HTTPException(status_code=404, detail="Service provider not found")

    file_urls = []

    # ==========================
    # Upload Photo to Supabase (same as signup)
    # ==========================
    if photo and photo.filename:

        # (Optional) only images allowed
        if not photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files allowed")

        file_extension = photo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"

        file_bytes = await photo.read()

        try:
            supabase.storage.from_("user-photos").upload(
                path=f"photos/{filename}",
                file=file_bytes,
                file_options={"content-type": photo.content_type}
            )

            public_url = supabase.storage.from_("user-photos").get_public_url(f"photos/{filename}")

            file_urls.append(public_url)

        except StorageApiError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Photo upload failed: {str(exc)}"
            )

    # 4. SAVE TO DB
    new_app = Application(
        client_id=current_user.id,
        provider_id=provider_id,
        message=message,
        photo=json.dumps(file_urls),  # store URL instead of filename
        status="pending"
    )

    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return {
        "message": "Application sent successfully",
        "data": format_app_response(new_app, request)
    }
# ==========================
# PROVIDER → VIEW APPLICATIONS
# ==========================
@router.get("/provider/applications")
def get_provider_applications(
    request: Request,
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.lower() != "service_provider":
        raise HTTPException(status_code=403, detail="Only providers allowed")

    query = db.query(Application).filter(
        Application.provider_id == current_user.id
    )

    if status:
        if status not in ["pending", "accepted", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status")

        query = query.filter(Application.status == status)

    apps = query.order_by(Application.created_at.desc()).all()

    return [format_app_response(app, request) for app in apps]


# ==========================
# PROVIDER → UPDATE STATUS
# ==========================
@router.put("/provider/update/{app_id}")
def update_status(
    app_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(Application).filter(Application.id == app_id).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.id != app.provider_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    app.status = status
    db.commit()

    return {
        "message": f"Application {status}",
        "application_id": app_id
    }


# ==========================
# CLIENT → SENT APPLICATIONS
# ==========================
@router.get("/client/sent")
def get_client_sent(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.lower() != "client":
        raise HTTPException(status_code=403, detail="Only clients allowed")

    apps = db.query(Application).filter(
        Application.client_id == current_user.id
    ).order_by(Application.created_at.desc()).all()

    return [format_app_response(app, request) for app in apps]


# ==========================
# CLIENT → FILTER BY STATUS
# ==========================
@router.get("/client/status")
def get_client_status(
    request: Request,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.lower() != "client":
        raise HTTPException(status_code=403, detail="Only clients allowed")

    apps = db.query(Application).filter(
        Application.client_id == current_user.id,
        Application.status == status
    ).order_by(Application.created_at.desc()).all()

    return [format_app_response(app, request) for app in apps]