from pydantic import BaseModel
from typing import Optional


class CreateDocument(BaseModel):
    document_type: Optional[str] = None   # aadhar, pan, etc
    document_number: Optional[str] = None