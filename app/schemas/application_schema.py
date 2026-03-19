from pydantic import BaseModel
from typing import Optional


class CreateApplication(BaseModel):
    message: str
    photo: Optional[str] = None