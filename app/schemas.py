from datetime import datetime

from pydantic import BaseModel


class NoteCreateRequest(BaseModel):
    text: str


class NoteResponse(BaseModel):
    id: int
    text: str
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
