import os
import uuid
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.core.security import get_current_user
from app.models.application_model import Application
from app.models.user_model import User
from app.core.supabase import supabase
from storage3.exceptions import StorageApiError

# ==========================
# ROUTER
# ==========================
router = APIRouter(prefix="/applications", tags=["Applications"])

# ==========================
# RESPONSE FORMATTER
# ==========================
def format_app_response(app_obj, request: Request = None):
    photo_urls = json.loads(app_obj.photo) if app_obj.photo else []

    return {
        "id": app_obj.id,
        "client_id": app_obj.client_id,
        "provider_id": app_obj.provider_id,
        "message": app_obj.message,
        "photo": photo_urls,
        "status": app_obj.status,
        "created_at": app_obj.created_at
    }

# ==========================
# CLIENT → SEND APPLICATION
# ==========================
@router.post("/client_send")
async def create_application(
    request: Request,
    provider_id: int = Form(...),
    message: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ROLE CHECK
    if current_user.role.lower() != "client":
        raise HTTPException(status_code=403, detail="Only clients can send applications")

    # PROVIDER CHECK
    provider = db.query(User).filter(User.id == provider_id).first()
    if not provider or provider.role.lower() != "service_provider":
        raise HTTPException(status_code=404, detail="Service provider not found")

    file_urls = []

    # FILE UPLOAD (SUPABASE)
    if photo and photo.filename:
        if not photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files allowed")

        filename = f"{uuid.uuid4()}.{photo.filename.split('.')[-1]}"
        file_bytes = await photo.read()

        try:
            supabase.storage.from_("user-photos").upload(
                path=f"applications/{filename}",
                file=file_bytes,
                file_options={"content-type": photo.content_type}
            )

            public_url = supabase.storage.from_("user-photos").get_public_url(
                f"applications/{filename}"
            )

            file_urls.append(public_url)

        except StorageApiError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Photo upload failed: {str(exc)}"
            )

    # SAVE TO DB
    new_app = Application(
        client_id=current_user.id,
        provider_id=provider_id,
        message=message,
        photo=json.dumps(file_urls),
        status="pending"
    )

    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return {
        "message": "Application created successfully",
        "data": format_app_response(new_app, request)
    }

# ==========================
# CLIENT → GET SENT APPLICATIONS
# ==========================
@router.get("/client")
def get_client_applications(
    request: Request,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.lower() != "client":
        raise HTTPException(status_code=403, detail="Only clients allowed")

    query = db.query(Application).filter(
        Application.client_id == current_user.id
    )

    if status:
        if status not in ["pending", "accepted", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        query = query.filter(Application.status == status)

    apps = query.order_by(Application.created_at.desc()).all()

    return [format_app_response(app, request) for app in apps]

# ==========================
# PROVIDER → GET RECEIVED APPLICATIONS
# ==========================
@router.get("/provider")
def get_provider_applications(
    request: Request,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.lower() != "service_provider":
        raise HTTPException(status_code=403, detail="Only service providers allowed")

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
# PROVIDER → UPDATE APPLICATION STATUS
# ==========================
@router.patch("/{app_id}/status")
def update_application_status(
    app_id: int,
    status: str = Form(...),
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