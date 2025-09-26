import json
import asyncio
import logging
from typing import Dict, Set
from sqlalchemy.orm import Session
from api.v1.services.project.chat_service import ChatService
from api.v1.schemas.project.chat_schema import ChatCreate
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, status
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("websocket")

# 프로젝트 및 채널별 연결 관리: {project_id: {channel_id: {user_id: WebSocket}}}
active_connections: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}

# 사용자별 채널 관리: {user_id: Set[(project_id, channel_id)]}
user_channels: Dict[str, Set[tuple]] = {}



async def get_channel_connections(project_id: str, channel_id: str) -> Dict[str, WebSocket]:
    """프로젝트와 채널의 활성 연결을 반환합니다."""
    return active_connections.get(project_id, {}).get(channel_id, {})

async def get_channel_users(project_id: str, channel_id: str) -> list:
    """프로젝트와 채널의 활성 사용자 ID 목록을 반환합니다."""
    connections = await get_channel_connections(project_id, channel_id)
    return list(connections.keys())

async def register_connection(project_id: str, channel_id: str, user_id: str, websocket: WebSocket) -> bool:
    """사용자의 웹소켓 연결을 등록합니다. 이미 있는 연결은 종료하고 새로운 연결로 대체합니다."""
    try:
        # 프로젝트, 채널 및 사용자 연결 추적 구조 초기화
        if project_id not in active_connections:
            active_connections[project_id] = {}
        if channel_id not in active_connections[project_id]:
            active_connections[project_id][channel_id] = {}
        
        if user_id not in user_channels:
            user_channels[user_id] = set()
        
        # 이미 존재하는 연결 종료
        if user_id in active_connections[project_id][channel_id]:
            old_websocket = active_connections[project_id][channel_id][user_id]
            try:
                await old_websocket.close(code=1000, reason="New connection established")
                logger.info(f"사용자 {user_id}의 이전 연결을 종료했습니다. (프로젝트: {project_id}, 채널: {channel_id})")
            except Exception as e:
                logger.error(f"이전 연결 종료 오류: {e}")
        
        # 새 연결 등록
        active_connections[project_id][channel_id][user_id] = websocket
        user_channels[user_id].add((project_id, channel_id))
        
        # 현재 채널 연결 정보 로깅
        users = await get_channel_users(project_id, channel_id)
        logger.info(f"프로젝트 {project_id}, 채널 {channel_id} 연결 등록 완료. 현재 사용자: {users} (총 {len(users)}명)")
        return True
    
    except Exception as e:
        logger.error(f"연결 등록 오류: {e}")
        return False

async def unregister_connection(project_id: str, channel_id: str, user_id: str) -> None:
    """사용자의 웹소켓 연결을 제거합니다."""
    try:
        # 채널에서 사용자 제거
        if project_id in active_connections and channel_id in active_connections[project_id] and user_id in active_connections[project_id][channel_id]:
            del active_connections[project_id][channel_id][user_id]
            logger.info(f"사용자 {user_id}가 프로젝트 {project_id}, 채널 {channel_id}에서 연결 해제됨")
            
            # 빈 채널 정리
            if not active_connections[project_id][channel_id]:
                del active_connections[project_id][channel_id]
                logger.info(f"프로젝트 {project_id}, 채널 {channel_id}에 연결된 사용자가 없어 채널 정리됨")
                
                # 빈 프로젝트 정리
                if not active_connections[project_id]:
                    del active_connections[project_id]
                    logger.info(f"프로젝트 {project_id}에 연결된 채널이 없어 프로젝트 정리됨")
        
        # 사용자의 채널 목록에서 제거
        if user_id in user_channels:
            user_channels[user_id].discard((project_id, channel_id))
            if not user_channels[user_id]:
                del user_channels[user_id]
                logger.info(f"사용자 {user_id}가 모든 채널에서 연결 해제됨")
        
        # 현재 채널 연결 정보 로깅
        if project_id in active_connections and channel_id in active_connections[project_id]:
            users = await get_channel_users(project_id, channel_id)
            logger.info(f"프로젝트 {project_id}, 채널 {channel_id} 업데이트됨. 현재 사용자: {users} (총 {len(users)}명)")
    
    except Exception as e:
        logger.error(f"연결 해제 오류: {e}")

async def broadcast_message(new_chat) -> None:
    """채널 내 모든 연결된 사용자에게 메시지를 브로드캐스트합니다."""
    if new_chat.project_id not in active_connections or new_chat.channel_id not in active_connections[new_chat.project_id]:
        return
    
    disconnected_users = []
    
    # 메시지 브로드캐스트 및 연결 유효성 확인
    for user_id, websocket in list(active_connections[new_chat.project_id][new_chat.channel_id].items()):
        try:
            # Chat 객체를 JSON으로 변환하여 전송
            chat_data = {
                "id": new_chat.id,
                "project_id": new_chat.project_id,
                "channel_id": new_chat.channel_id,
                "user_id": new_chat.user_id,
                "message": new_chat.message,
                "timestamp": new_chat.timestamp.isoformat() if new_chat.timestamp else None
            }
            await websocket.send_text(json.dumps(chat_data))
        except Exception as e:
            logger.error(f"사용자 {user_id}에게 메시지 전송 실패: {e}")
            disconnected_users.append(user_id)
    
    # 연결이 끊긴 사용자 정리
    for user_id in disconnected_users:
        await unregister_connection(new_chat.project_id, new_chat.channel_id, user_id)

async def publish_system_message(project_id: str, channel_id: str, message: str) -> None:
    """시스템 메시지를 채널에 직접 브로드캐스트합니다."""
    try:
        # 시스템 메시지를 위한 임시 객체 생성
        system_chat = type('SystemChat', (), {
            'project_id': project_id,
            'channel_id': channel_id,
            'id': f"system_{datetime.now().timestamp()}",
            'user_id': 0,
            'message': message,
            'timestamp': datetime.now()
        })()
        await broadcast_message(system_chat)
    except Exception as e:
        logger.error(f"시스템 메시지 발행 오류: {e}")

async def websocket_handler(websocket: WebSocket, channel_id: str, project_id: str, user_id: int, db: Session) -> None:
    """웹소켓 연결을 처리합니다."""
    
    try:
        # WebSocket 연결 수락
        await websocket.accept()
        logger.info(f"사용자 {user_id}가 프로젝트 {project_id}, 채널 {channel_id}에 연결 시도 중")
        
        # 연결 등록
        registration_success = await register_connection(project_id, channel_id, str(user_id), websocket)
        if not registration_success:
            logger.error(f"사용자 {user_id} 등록 실패")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="연결 등록 실패")
            return
        
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
                        logger.debug(f"핑 메시지 전송: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}")
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
                            logger.debug(f"퐁 응답 수신: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}")
                            continue
                        
                        # 필드 검증 로직 수정 - 클라이언트가 보내는 형식과 일치시킴
                        if not all(k in message_data for k in ["project_id", "channel_id", "message"]):
                            logger.warning(f"잘못된 메시지 형식: {data[:100]}...")
                            continue
                        
                        # 프로젝트 ID와 채널 ID 일치 확인
                        if message_data["project_id"] != project_id or message_data["channel_id"] != channel_id:
                            logger.warning(f"메시지의 프로젝트/채널 ID 불일치: 요청={project_id}/{channel_id}, 메시지={message_data['project_id']}/{message_data['channel_id']}")
                            continue
                        
                        # 로깅 - 메시지 내용은 보안상 일부만 표시
                        msg_preview = message_data.get("message", "")[:50]
                        if len(message_data.get("message", "")) > 50:
                            msg_preview += "..."
                        
                        logger.info(
                            f"메시지 수신: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}, "
                            f"내용={msg_preview}"
                        )
                        

                        # === DB에 채팅 메시지 저장 ===
                        try:
                            # user_id, projectId, channelId는 str일 수 있으므로 타입 변환
                            db_user_id = int(user_id)
                            db_project_id = str(project_id)
                            db_channel_id = str(channel_id)
                            db_message = message_data.get("message", "")
                            
                            service = ChatService(db)
                            new_chat = service.create(project_id, channel_id, db_user_id, ChatCreate(message=db_message))
                            
                            # 메시지 직접 브로드캐스트
                            await broadcast_message(new_chat)
                        except Exception as e:
                            logger.error(f"채팅 메시지 DB 저장 오류: {e}")
                        # === DB 저장 끝 ===

                        # # 채널의 다른 사용자에게 알림 전송
                        # try:
                        #     channel_members = ChannelCRUD.get_channel_by_channel_id(db, channel_id).member_id
                        #     sender_id = int(user_id)
                        #     sender_name = message_data.get("user", "알 수 없는 사용자")
                        #     logger.info(f"{message_data}")
                            
                        #     notification_tasks = []
                        #     for member_id in channel_members:
                        #         if member_id != sender_id:
                        #             notification_id = int(datetime.now().timestamp() * 1000)
                        #             notification_tasks.append(
                        #                 send_notification(
                        #                     db=db,
                        #                     id=notification_id,
                        #                     title=f"{sender_name}님의 새로운 메시지",
                        #                     message=message_data.get("message", ""),
                        #                     type="chat",
                        #                     isRead=False,
                        #                     sender_id=sender_id,
                        #                     receiver_id=member_id,
                        #                     project_id=project_id
                        #                 )
                        #             )
                            
                        #     if notification_tasks:
                        #         await asyncio.gather(*notification_tasks)
                        #         logger.info(f"{len(notification_tasks)}명에게 알림을 전송했습니다.")

                        # except Exception as e:
                        #     logger.error(f"알림 전송 중 오류 발생: {e}")
                        
                    except json.JSONDecodeError:
                        logger.error(f"잘못된 JSON 형식: {data[:100]}...")
                    except Exception as e:
                        logger.error(f"메시지 처리 오류: {e}")
                
                except asyncio.TimeoutError:
                    # 타임아웃은 정상 - 핑 체크를 위한 루프 계속
                    pass
                except WebSocketDisconnect:
                    logger.info(f"웹소켓 연결 끊김: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}")
                    break
                except Exception as e:
                    logger.error(f"웹소켓 수신 오류: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}, 오류={e}")
                    break
        
        except Exception as e:
            logger.error(f"메시지 루프 오류: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}, 오류={e}")
    
    except WebSocketDisconnect:
        logger.info(f"웹소켓 연결이 클라이언트에 의해 종료됨: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}")
    except Exception as e:
        logger.error(f"웹소켓 핸들러 오류: {e}")
    
    finally:
        logger.info(f"연결 종료 처리 시작: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}")
        # 연결 종료 처리
        if user_id:
            await unregister_connection(project_id, channel_id, str(user_id))
            
            # # 퇴장 메시지
            # try:
            #     await publish_system_message(projectId, channelId, f"{user_id} 님이 채팅방을 나갔습니다.")
            # except Exception as e:
            #     logger.error(f"퇴장 메시지 발행 오류: {e}")
        
        # 연결 정리가 이미 unregister_connection에서 처리됨
        
        logger.info(f"웹소켓 핸들러 종료: 프로젝트={project_id}, 채널={channel_id}, 사용자={user_id}")
