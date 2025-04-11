from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import SessionLocal, engine
from models.chat import Base
from websocket.chat import websocket_handler
from schemas.chat import ChatCreate
from crud.chat import save_chat_message, get_chat_history

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.websocket("/ws/chat/{channelId}")
async def chat_endpoint(websocket: WebSocket, channelId: str):
    try:
        await websocket.accept()
        logging.info(f"WebSocket connection established for channel: {channelId}")
        await websocket_handler(websocket, channelId)
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for channel: {channelId}")
    except Exception as e:
        logging.error(f"WebSocket error in channel {channelId}: {str(e)}")
        try:
            await websocket.close()
        except:
            pass


@app.post("/chat/")
def post_message(chat: ChatCreate, db: SessionLocal = Depends(get_db)):
    return save_chat_message(db, chat)


@app.get("/chat/{channelId}")
def get_messages(channelId: str, db: SessionLocal = Depends(get_db)):
    return get_chat_history(db, channelId)
