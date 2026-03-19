from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid

from app.core.security import get_current_user
from app.dependencies.db import get_db
from app.core.supabase import supabase
from app.models.profile_document_model import Document


# ==========================
# ROUTER
# ==========================
router = APIRouter(prefix="/documents", tags=["Documents"])


# ==========================
# UPLOAD DOCUMENT (ONLY SERVICE PROVIDER)
# ==========================
@router.post("/upload")
def upload_document(
    document_type: str = Form(...),
    document_number: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # only service_provider allowed
    if current_user.role != "service_provider":
        raise HTTPException(
            status_code=403,
            detail="Only service providers can upload documents"
        )

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    file_bytes = file.file.read()

    try:
        # upload to supabase
        supabase.storage.from_("user-photos").upload(
            path=f"documents/{filename}",
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )

        # get public url
        file_url = supabase.storage.from_("user-photos").get_public_url(
            f"documents/{filename}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Upload failed: {str(e)}"
        )

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
        },
    }


# ==========================
# GET MY DOCUMENTS (ANY USER)
# ==========================
@router.get("/my-documents")
def get_my_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    docs = db.query(Document).filter(
        Document.userId == current_user.id
    ).all()

    return {
        "documents": [
            {
                "id": d.id,
                "document_type": d.document_type,
                "document_number": d.document_number,
                "file_url": d.file_url,
            }
            for d in docs
        ]
    }


# ==========================
# CLIENT → VIEW PROVIDER DOCUMENTS
# ==========================
@router.get("/provider/{provider_id}")
def get_provider_documents(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # only client allowed
    if current_user.role != "client":
        raise HTTPException(
            status_code=403,
            detail="Only clients can view provider documents"
        )

    docs = db.query(Document).filter(
        Document.userId == provider_id
    ).all()

    return {
        "documents": [
            {
                "id": d.id,
                "document_type": d.document_type,
                "file_url": d.file_url,
            }
            for d in docs
        ]
    }


# ==========================
# DELETE DOCUMENT (ONLY OWNER)
# ==========================
@router.delete("/delete/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == doc_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.userId != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully"}
