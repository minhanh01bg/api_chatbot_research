from pydantic import BaseModel

class Langgraph_adaptive_schema(BaseModel):
    question: str
    session_id: str = "user_test"

from pydantic import BaseModel
from pydantic import Field
from typing import List, Optional
from typing import List, Dict
from datetime import datetime


class Chat(BaseModel):
    question: str
    session_id: str = "user_test"
    chat_history: List[Dict[str, str]]


class SuggestPrompt(BaseModel):
    chat_history: List[Dict[str, str]]


class ChatMessage(BaseModel):
    role: str = Field(...,
                      description="The role of the message sender (system/user/assistant)")
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(
        None, description="Optional name for the message sender")


class MessageBase(BaseModel):
    role: str
    content: str
    updated_time: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    session_id: str
    created_time: datetime = Field(default_factory=datetime.utcnow)
    updated_time: datetime = Field(default_factory=datetime.utcnow)
    messages: List[MessageBase] = []


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int


class ChatHistoryResponse(BaseModel):
    session_id: str
    data: List[MessageBase] 


class SessionData(BaseModel):
    _id: str
    session_id: str
    created_time: datetime
    updated_time: datetime
    # messages: List[MessageBase]
    first_question: Optional[str]
    question_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "_id": "example_id"
            }
        }
        populate_by_name = True
        arbitrary_types_allowed = True


class SessionResponse(PaginatedResponse):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    data: List[SessionData]
