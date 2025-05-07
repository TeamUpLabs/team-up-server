from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from database import SessionLocal
import logging
from websocket.chat import websocket_handler
from schemas.chat import ChatCreate
from crud.chat import save_chat_message, get_chat_history

router = APIRouter(
    tags=["chat"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.websocket("/ws/chat/{projectId}/{channelId}")
async def chat_endpoint(websocket: WebSocket, projectId: str, channelId: str):
    try:
        logging.info(f"WebSocket connection established for project: {projectId}, channel: {channelId}")
        await websocket_handler(websocket, channelId, projectId)
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for project: {projectId}, channel: {channelId}")
    except Exception as e:
        logging.error(f"WebSocket error in project {projectId}, channel {channelId}: {str(e)}")
        try:
            await websocket.close()
        except:
            pass

@router.post("/chat")
def post_message(chat: ChatCreate, db: SessionLocal = Depends(get_db)):
    return save_chat_message(db, chat)

@router.get("/chat/{projectId}/{channelId}")
def get_messages(projectId: str, channelId: str, db: SessionLocal = Depends(get_db)):
    return get_chat_history(db, projectId, channelId) 