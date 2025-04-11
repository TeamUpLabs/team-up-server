from pydantic import BaseModel
from typing import Optional

class ChatCreate(BaseModel):
    channelId: str
    userId: int
    user: str
    message: str
    timestamp: str

class Chat(BaseModel):
    id: int
    channelId: str
    user: str
    message: str
    timestamp: str

    class Config:
        orm_mode = True