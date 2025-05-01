import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("websocket")

# Redis 클라이언트 설정
try:
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
except Exception as e:
    logger.error(f"Redis 연결 실패: {e}")
    raise

# 채널별 연결 관리: {channel_id: {user_id: WebSocket}}
active_connections: Dict[str, Dict[str, WebSocket]] = {}

# 사용자별 채널 관리: {user_id: Set[channel_id]}
user_channels: Dict[str, Set[str]] = {}

# Redis 연결 상태 체크
async def check_redis_connection() -> bool:
    """Redis 서버 연결 상태를 확인합니다."""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis 서버 연결 실패: {e}")
        return False

async def get_channel_connections(channel_id: str) -> Dict[str, WebSocket]:
    """채널의 활성 연결을 반환합니다."""
    return active_connections.get(channel_id, {})

async def get_channel_users(channel_id: str) -> list:
    """채널의 활성 사용자 ID 목록을 반환합니다."""
    connections = await get_channel_connections(channel_id)
    return list(connections.keys())

async def register_connection(channel_id: str, user_id: str, websocket: WebSocket) -> bool:
    """사용자의 웹소켓 연결을 등록합니다. 이미 있는 연결은 종료하고 새로운 연결로 대체합니다."""
    try:
        # 채널 및 사용자 연결 추적 구조 초기화
        if channel_id not in active_connections:
            active_connections[channel_id] = {}
        
        if user_id not in user_channels:
            user_channels[user_id] = set()
        
        # 이미 존재하는 연결 종료
        if user_id in active_connections[channel_id]:
            old_websocket = active_connections[channel_id][user_id]
            try:
                await old_websocket.close(code=1000, reason="New connection established")
                logger.info(f"사용자 {user_id}의 이전 연결을 종료했습니다. (채널: {channel_id})")
            except Exception as e:
                logger.error(f"이전 연결 종료 오류: {e}")
        
        # 새 연결 등록
        active_connections[channel_id][user_id] = websocket
        user_channels[user_id].add(channel_id)
        
        # 현재 채널 연결 정보 로깅
        users = await get_channel_users(channel_id)
        logger.info(f"채널 {channel_id} 연결 등록 완료. 현재 사용자: {users} (총 {len(users)}명)")
        return True
    
    except Exception as e:
        logger.error(f"연결 등록 오류: {e}")
        return False

async def unregister_connection(channel_id: str, user_id: str) -> None:
    """사용자의 웹소켓 연결을 제거합니다."""
    try:
        # 채널에서 사용자 제거
        if channel_id in active_connections and user_id in active_connections[channel_id]:
            del active_connections[channel_id][user_id]
            logger.info(f"사용자 {user_id}가 채널 {channel_id}에서 연결 해제됨")
            
            # 빈 채널 정리
            if not active_connections[channel_id]:
                del active_connections[channel_id]
                logger.info(f"채널 {channel_id}에 연결된 사용자가 없어 채널 정리됨")
        
        # 사용자의 채널 목록에서 제거
        if user_id in user_channels:
            user_channels[user_id].discard(channel_id)
            if not user_channels[user_id]:
                del user_channels[user_id]
                logger.info(f"사용자 {user_id}가 모든 채널에서 연결 해제됨")
        
        # 현재 채널 연결 정보 로깅
        if channel_id in active_connections:
            users = await get_channel_users(channel_id)
            logger.info(f"채널 {channel_id} 업데이트됨. 현재 사용자: {users} (총 {len(users)}명)")
    
    except Exception as e:
        logger.error(f"연결 해제 오류: {e}")

async def broadcast_message(channel_id: str, message: str) -> None:
    """채널 내 모든 연결된 사용자에게 메시지를 브로드캐스트합니다."""
    if channel_id not in active_connections:
        return
    
    disconnected_users = []
    
    # 메시지 브로드캐스트 및 연결 유효성 확인
    for user_id, websocket in list(active_connections[channel_id].items()):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"사용자 {user_id}에게 메시지 전송 실패: {e}")
            disconnected_users.append(user_id)
    
    # 연결이 끊긴 사용자 정리
    for user_id in disconnected_users:
        await unregister_connection(channel_id, user_id)

async def publish_system_message(channel_id: str, message: str) -> None:
    """시스템 메시지를 Redis에 발행합니다."""
    try:
        system_msg = {
            "id": f"system_{datetime.now().timestamp()}",
            "channelId": channel_id,
            "userId": 0,
            "user": "System",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "type": "system",
            "senderName": "System"
        }
        await redis_client.publish(channel_id, json.dumps(system_msg))
    except Exception as e:
        logger.error(f"시스템 메시지 발행 오류: {e}")

async def websocket_handler(websocket: WebSocket, channelId: str) -> None:
    """웹소켓 연결을 처리합니다."""
    # 사용자 ID 확인
    user_id = None
    pubsub = None
    redis_listener_task = None
    
    try:
        user_id = websocket.query_params.get("user_id")
        if not user_id:
            logger.error("웹소켓 연결에 user_id 파라미터가 없습니다.")
            await websocket.accept()  # 연결을 일단 수락하고 오류 메시지 전송 후 종료
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="사용자 ID가 필요합니다")
            return
        
        # WebSocket 연결 수락
        await websocket.accept()
        logger.info(f"사용자 {user_id}가 채널 {channelId}에 연결 시도 중")
        
        # Redis 연결 확인
        if not await check_redis_connection():
            logger.error("Redis 서버에 연결할 수 없습니다")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="서버 내부 오류")
            return
        
        # Redis 구독 설정 - 연결 등록 전에 이동
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channelId)
        logger.info(f"Redis 채널 {channelId} 구독 시작")
        
        # 연결 등록
        registration_success = await register_connection(channelId, user_id, websocket)
        if not registration_success:
            logger.error(f"사용자 {user_id} 등록 실패")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="연결 등록 실패")
            if pubsub:
                await pubsub.unsubscribe(channelId)
            return
        
        # # 입장 메시지
        # await publish_system_message(channelId, f"{user_id} 님이 채팅방에 입장했습니다.")
        
        # Redis 메시지 수신 리스너 태스크
        async def redis_listener():
            try:
                logger.info(f"Redis 리스너 시작: 채널={channelId}, 사용자={user_id}")
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        logger.debug(f"Redis 메시지 수신: {message['data'][:50]}...")
                        await broadcast_message(channelId, message["data"])
            except asyncio.CancelledError:
                logger.info(f"Redis 리스너 태스크 취소됨 (채널: {channelId}, 사용자: {user_id})")
                raise
            except Exception as e:
                logger.error(f"Redis 리스너 오류: {e}")
        
        # 리스너 태스크 시작
        redis_listener_task = asyncio.create_task(redis_listener())
        logger.info(f"메시지 수신 대기 시작: 채널={channelId}, 사용자={user_id}")
        
        # 클라이언트로부터 메시지 수신 대기
        try:
            # 핑-퐁 메시지 주기
            ping_interval = 30  # 30초마다 핑
            last_ping_time = asyncio.get_event_loop().time()
            
            while True:
                # 핑-퐁 메시지와 일반 메시지 수신을 동시에 처리
                current_time = asyncio.get_event_loop().time()
                if current_time - last_ping_time > ping_interval:
                    try:
                        # 핑 메시지 전송으로 연결 유지
                        logger.debug(f"핑 메시지 전송: 채널={channelId}, 사용자={user_id}")
                        await websocket.send_text(json.dumps({"type": "ping"}))
                        last_ping_time = current_time
                    except Exception as e:
                        logger.error(f"핑 메시지 전송 실패: {e}")
                        break
                
                # 타임아웃과 함께 메시지 수신 대기
                try:
                    # 1초 타임아웃으로 receive_text 호출
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=1.0
                    )
                    
                    # 메시지 처리
                    try:
                        # 메시지 파싱 및 검증
                        message_data = json.loads(data)
                        
                        # 핑-퐁 응답 처리
                        if message_data.get("type") == "pong":
                            logger.debug(f"퐁 응답 수신: 채널={channelId}, 사용자={user_id}")
                            continue
                        
                        # 필드 검증 로직 수정 - 클라이언트가 보내는 형식과 일치시킴
                        if not all(k in message_data for k in ["id", "channelId", "message"]):
                            logger.warning(f"잘못된 메시지 형식: {data[:100]}...")
                            continue
                        
                        # 로깅 - 메시지 내용은 보안상 일부만 표시
                        msg_preview = message_data.get("message", "")[:50]
                        if len(message_data.get("message", "")) > 50:
                            msg_preview += "..."
                        
                        logger.info(
                            f"메시지 수신: 채널={channelId}, 사용자={user_id}, "
                            f"메시지 ID={message_data.get('id')}, 내용={msg_preview}"
                        )
                        
                        # Redis에 메시지 발행
                        await redis_client.publish(channelId, data)
                        
                    except json.JSONDecodeError:
                        logger.error(f"잘못된 JSON 형식: {data[:100]}...")
                    except Exception as e:
                        logger.error(f"메시지 처리 오류: {e}")
                
                except asyncio.TimeoutError:
                    # 타임아웃은 정상 - 핑 체크를 위한 루프 계속
                    pass
                except WebSocketDisconnect:
                    logger.info(f"웹소켓 연결 끊김: 채널={channelId}, 사용자={user_id}")
                    break
                except Exception as e:
                    logger.error(f"웹소켓 수신 오류: 채널={channelId}, 사용자={user_id}, 오류={e}")
                    break
        
        except Exception as e:
            logger.error(f"메시지 루프 오류: 채널={channelId}, 사용자={user_id}, 오류={e}")
    
    except WebSocketDisconnect:
        logger.info(f"웹소켓 연결이 클라이언트에 의해 종료됨: 채널={channelId}, 사용자={user_id}")
    except Exception as e:
        logger.error(f"웹소켓 핸들러 오류: {e}")
    
    finally:
        logger.info(f"연결 종료 처리 시작: 채널={channelId}, 사용자={user_id}")
        # 연결 종료 처리
        if user_id:
            await unregister_connection(channelId, user_id)
            
            # # 퇴장 메시지
            # try:
            #     await publish_system_message(channelId, f"{user_id} 님이 채팅방을 나갔습니다.")
            # except Exception as e:
            #     logger.error(f"퇴장 메시지 발행 오류: {e}")
        
        # Redis 구독 해제
        if pubsub:
            try:
                await pubsub.unsubscribe(channelId)
                logger.info(f"Redis 채널 {channelId} 구독 해제됨")
            except Exception as e:
                logger.error(f"Redis 구독 해제 오류: {e}")
        
        # 리스너 태스크 취소
        if redis_listener_task:
            redis_listener_task.cancel()
            try:
                await redis_listener_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"웹소켓 핸들러 종료: 채널={channelId}, 사용자={user_id}")
