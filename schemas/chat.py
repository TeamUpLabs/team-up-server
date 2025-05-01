from pydantic import BaseModel
from typing import Optional

class ChatCreate(BaseModel):
    projectId: str
    channelId: str
    userId: int
    user: str
    message: str
    timestamp: str

class Chat(BaseModel):
    id: int
    projectId: str
    channelId: str
    user: str
    message: str
    timestamp: str

    class Config:
        orm_mode = True