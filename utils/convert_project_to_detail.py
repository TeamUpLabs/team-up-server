from models.project import Project
from schemas.project import ProjectDetail
from schemas.project import ProjectMember
from crud import project
from sqlalchemy.orm import Session
from schemas.user import UserBrief, UserDetail
from schemas.milestone import MilestoneDetail
from schemas.task import TaskDetail
from schemas.schedule import ScheduleResponse
from schemas.channel import ChannelResponse, ChannelMemberResponse
from schemas.chat import ChatResponse
from schemas.whiteboard import WhiteBoardDetail
from schemas.participation_request import ParticipationRequestResponse
from datetime import datetime

def convert_project_to_project_detail(db_project: Project, db: Session) -> ProjectDetail:
    """SQLAlchemy Project 모델을 ProjectDetail 스키마로 변환"""
    # 기본 정보만 먼저 추출하여 Pydantic 모델 생성
    # members와 같은 관계형 필드 제외
    project_data = {
        "id": db_project.id,
        "title": db_project.title,
        "description": db_project.description,
        "project_type": db_project.project_type,
        "location": db_project.location,
        "status": db_project.status,
        "visibility": db_project.visibility,
        "team_size": db_project.team_size,
        "start_date": db_project.start_date,
        "end_date": db_project.end_date,
        "tags": db_project.tags,
        "github_url": db_project.github_url,
        "created_at": db_project.created_at,
        "updated_at": db_project.updated_at,
        "completed_at": db_project.completed_at
    }
    
    # 소유자 정보 추가
    if db_project.owner:
        project_data["owner"] = UserBrief.model_validate(db_project.owner, from_attributes=True)
    
    # 프로젝트 상세 정보 생성
    project_detail = ProjectDetail(**project_data)
    
    # 멤버 정보 구성
    member_info = project.get_project_members(db=db, project_id=db_project.id)
    project_detail.members = []
    for m in member_info:
        user_detail = UserDetail.model_validate(m["user"], from_attributes=True)
            
        project_detail.members.append(
            ProjectMember(
                user=user_detail,
                role=m["role"],
                is_leader=m["is_leader"],
                is_manager=m["is_manager"],
                joined_at=m["joined_at"]
            )
        )
    
    # 태스크 정보 추가
    tasks = []
    if db_project.tasks:
        for task in db_project.tasks:
            tasks.append(TaskDetail.model_validate(task, from_attributes=True))
            
    project_detail.tasks = tasks
    
    
    milestones = []
    if db_project.milestones:
        for milestone in db_project.milestones:
            milestones.append(MilestoneDetail.model_validate(milestone, from_attributes=True))
    project_detail.milestones = milestones
    
    # 참여 요청 정보 추가
    participation_requests = []
    if db_project.participation_requests:
        for req in db_project.participation_requests:
            participation_requests.append(ParticipationRequestResponse.model_validate(req, from_attributes=True))
    project_detail.participation_requests = participation_requests
    
    # 스케줄 정보 추가
    schedules = []
    if db_project.schedules:
        for schedule in db_project.schedules:
            schedules.append(ScheduleResponse.model_validate(schedule, from_attributes=True))
    project_detail.schedules = schedules
    
    # 채널 정보 추가
    channels = []
    if db_project.channels:
        for channel in db_project.channels:
            # Create a dictionary of the channel data
            channel_data = {
                'project_id': channel.project_id,
                'channel_id': channel.channel_id,
                'name': channel.name,
                'description': channel.description,
                'is_public': channel.is_public,
                'created_at': channel.created_at,
                'updated_at': channel.updated_at,
                'created_by': channel.created_by,
                'updated_by': channel.updated_by,
                'member_count': len(channel.members) if hasattr(channel, 'members') else 0,
                'members': [
                    {
                        'id': getattr(member, 'id', None) or getattr(member, 'user_id', None) or (member.user.id if hasattr(member, 'user') else None),
                        'name': getattr(member, 'name', None) or (member.user.name if hasattr(member, 'user') else 'Unknown'),
                        'email': getattr(member, 'email', None) or (member.user.email if hasattr(member, 'user') else ''),
                        'profile_image': getattr(member, 'profile_image', None) or (getattr(member.user, 'profile_image', None) if hasattr(member, 'user') else None),
                        'role': getattr(member, 'role', 'member'),
                        'joined_at': getattr(member, 'joined_at', None) or getattr(member, 'created_at', None) or datetime.utcnow()
                    }
                    for member in channel.members if hasattr(channel, 'members')
                ],
                'chats': [],
                'chats_count': len(channel.chats) if hasattr(channel, 'chats') else 0
            }
            channels.append(ChannelResponse.model_validate(channel_data))
    project_detail.channels = channels
    
    # WhiteBoard 정보 추가
    whiteboards = []
    if db_project.whiteboards:
        for whiteboard in db_project.whiteboards:
            whiteboards.append(WhiteBoardDetail.model_validate(whiteboard, from_attributes=True))
    project_detail.whiteboards = whiteboards
    
    # 통계 정보 추가
    project_detail.task_count = len(db_project.tasks)
    project_detail.completed_task_count = len([t for t in db_project.tasks if t.status == "completed"])
    project_detail.milestone_count = len(db_project.milestones)
    project_detail.participation_request_total_count = len(db_project.participation_requests)
    project_detail.participation_request_accepted_count = len([request for request in db_project.participation_requests if request.status == "accepted"])
    project_detail.participation_request_rejected_count = len([request for request in db_project.participation_requests if request.status == "rejected"])
    project_detail.participation_request_pending_count = len([request for request in db_project.participation_requests if request.status == "pending"])
    project_detail.schedule_count = len(db_project.schedules)
    project_detail.channel_count = len(db_project.channels)
    project_detail.chat_count = len([chat for channel in db_project.channels for chat in channel.chats])
    project_detail.whiteboard_count = len(db_project.whiteboards)
    
    return project_detail