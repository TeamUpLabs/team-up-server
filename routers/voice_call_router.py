from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
from typing import Dict

router = APIRouter(
    prefix="/api/voice-call",
    tags=["voice-call"]
)

# Store for active WebRTC connections
active_connections: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}

@router.websocket("/ws")
async def voice_call_signaling(websocket: WebSocket, project_id: str, channel_id: str, user_id: str):
    await websocket.accept()
    
    # Store connection with project_id separation
    if project_id not in active_connections:
        active_connections[project_id] = {}
    if channel_id not in active_connections[project_id]:
        active_connections[project_id][channel_id] = {}
    active_connections[project_id][channel_id][user_id] = websocket

    try:
        # Notify others about new user joining
        join_message = {
            "type": "user-joined",
            "user_id": user_id
        }
        
        for other_user_id, conn in active_connections[project_id][channel_id].items():
            if other_user_id != user_id:
                await conn.send_text(json.dumps(join_message))
        
        # Listen for messages
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Handle different signal types
            if data["type"] == "offer" or data["type"] == "answer" or data["type"] == "ice-candidate":
                # Forward to the specific recipient
                target_id = data.get("target")
                if target_id and target_id in active_connections[project_id][channel_id]:
                    await active_connections[project_id][channel_id][target_id].send_text(message)
            
            elif data["type"] == "disconnect":
                # Notify others about user disconnecting
                break
    
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for project: {project_id}, channel: {channel_id}, user: {user_id}")
    except Exception as e:
        logging.error(f"WebSocket error in video call: {str(e)}")
    finally:
        # Remove connection on disconnect
        if project_id in active_connections and channel_id in active_connections[project_id] and user_id in active_connections[project_id][channel_id]:
            del active_connections[project_id][channel_id][user_id]
            
            # Notify others about user leaving
            leave_message = {
                "type": "user-left",
                "user_id": user_id
            }
            
            if project_id in active_connections and channel_id in active_connections[project_id]:
                for user_id, conn in active_connections[project_id][channel_id].items():
                    try:
                        await conn.send_text(json.dumps(leave_message))
                    except:
                        pass
                    
                # Clean up empty channels
                if not active_connections[project_id][channel_id]:
                    del active_connections[project_id][channel_id]
                    # Clean up empty projects
                    if not active_connections[project_id]:
                        del active_connections[project_id] 