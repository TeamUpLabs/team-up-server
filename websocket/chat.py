import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

connections = {}

def get_active_connections(channel_id: str) -> int:
    """Return the number of active connections in a channel"""
    if channel_id not in connections:
        return 0
    # Use correct WebSocket state check (DISCONNECTED = 3)
    connections[channel_id] = [conn for conn in connections[channel_id] if conn.client_state != 3]
    return len(connections[channel_id])

async def websocket_handler(websocket: WebSocket, channelId: str):
    print(f"🔌 Connection attempt to room {channelId}")
    
    if channelId not in connections:
        connections[channelId] = []
    connections[channelId].append(websocket)
    active_count = get_active_connections(channelId)
    print(f"👥 Current connections in room {channelId}: {active_count} users")

    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channelId)
    except Exception as e:
        print(f"❌ Redis subscription failed: {e}")
        if channelId in connections and websocket in connections[channelId]:
            connections[channelId].remove(websocket)
        return

    task = None
    try:
        async def redis_listener():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        for conn in connections.get(channelId, []):
                            try:
                                await conn.send_text(message["data"])
                            except Exception:
                                continue
            except Exception as e:
                print(f"Redis listener error: {e}")

        task = asyncio.create_task(redis_listener())

        while True:
            try:
                data = await websocket.receive_text()
                await redis_client.publish(channelId, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break

    finally:
        if channelId in connections and websocket in connections[channelId]:
            connections[channelId].remove(websocket)
            active_count = get_active_connections(channelId)
            print(f"👥 Updated connections in room {channelId}: {active_count} users")
        try:
            await pubsub.unsubscribe(channelId)
        except:
            pass
        if task:
            task.cancel()
        print(f"🔌 WebSocket disconnected from room {channelId}")
