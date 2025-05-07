from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
from typing import Dict, Any

router = APIRouter(
    tags=["video-call"]
)

# Store for active WebRTC connections
active_connections: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}

@router.websocket("/project/{project_id}/ws/call/{channelId}/{userId}")
async def video_call_signaling(websocket: WebSocket, project_id: str, channelId: str, userId: str):
    await websocket.accept()
    
    # Store connection with project_id separation
    if project_id not in active_connections:
        active_connections[project_id] = {}
    if channelId not in active_connections[project_id]:
        active_connections[project_id][channelId] = {}
    active_connections[project_id][channelId][userId] = websocket
    
    try:
        # Notify others about new user joining
        join_message = {
            "type": "user-joined",
            "userId": userId
        }
        
        for user_id, conn in active_connections[project_id][channelId].items():
            if user_id != userId:
                await conn.send_text(json.dumps(join_message))
        
        # Listen for messages
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Handle different signal types
            if data["type"] == "offer" or data["type"] == "answer" or data["type"] == "ice-candidate":
                # Forward to the specific recipient
                target_id = data.get("target")
                if target_id and target_id in active_connections[project_id][channelId]:
                    await active_connections[project_id][channelId][target_id].send_text(message)
            
            elif data["type"] == "disconnect":
                # Notify others about user disconnecting
                break
    
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for project: {project_id}, channel: {channelId}, user: {userId}")
    except Exception as e:
        logging.error(f"WebSocket error in video call: {str(e)}")
    finally:
        # Remove connection on disconnect
        if project_id in active_connections and channelId in active_connections[project_id] and userId in active_connections[project_id][channelId]:
            del active_connections[project_id][channelId][userId]
            
            # Notify others about user leaving
            leave_message = {
                "type": "user-left",
                "userId": userId
            }
            
            if project_id in active_connections and channelId in active_connections[project_id]:
                for user_id, conn in active_connections[project_id][channelId].items():
                    try:
                        await conn.send_text(json.dumps(leave_message))
                    except:
                        pass
                    
                # Clean up empty channels
                if not active_connections[project_id][channelId]:
                    del active_connections[project_id][channelId]
                    # Clean up empty projects
                    if not active_connections[project_id]:
                        del active_connections[project_id] 