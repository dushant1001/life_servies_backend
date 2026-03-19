from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid

from app.core.security import get_current_user
from app.dependencies.db import get_db
from app.models.user_model import User
from app.models.profile_document_model import Document
from app.core.supabase import supabase

router = APIRouter(prefix="/documents", tags=["Documents"])


# ==========================
# UPLOAD DOCUMENT
# ==========================
@router.post("/upload")
def upload_document(
    document_type: str = Form(...),
    document_number: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # 🔥 Only service provider allowed
    if current_user.role != "service_provider":
        raise HTTPException(status_code=403, detail="Only service providers can upload documents")

    # file name
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    file_bytes = file.file.read()

    try:
        # ✅ upload
        supabase.storage.from_("user-photos").upload(
            path=f"documents/{filename}",
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )

        # ✅ get public url (same bucket + same path)
        file_url = supabase.storage.from_("user-photos").get_public_url(
            f"documents/{filename}"
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

    # save in DB
    new_doc = Document(
        document_type=document_type,
        document_number=document_number,
        file_url=file_url,
        userId=current_user.id,
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {
        "message": "Document uploaded successfully",
        "data": {
            "id": new_doc.id,
            "document_type": new_doc.document_type,
            "file_url": new_doc.file_url,
            "status": new_doc.status,
        },
    }


# ==========================
# GET MY DOCUMENTS
# ==========================
@router.get("/get")
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    docs = db.query(Document).filter(Document.userId == current_user.id).all()

    return {
        "documents": [
            {
                "id": d.id,
                "document_type": d.document_type,
                "document_number": d.document_number,
                "file_url": d.file_url,
                "status": d.status,
            }
            for d in docs
        ]
    }


# ==========================
# DELETE DOCUMENT
# ==========================
@router.delete("/delete/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.userId == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully"}
