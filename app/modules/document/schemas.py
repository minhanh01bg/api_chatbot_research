from pydantic import BaseModel
from typing import List, Optional


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: str
    vectorstore_id: str
    filename: str


class DocumentSearchSchema(BaseModel):
    search_text: str
