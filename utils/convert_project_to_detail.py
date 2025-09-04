from models.project import Project
from schemas.project import ProjectDetail
from schemas.project import ProjectMember
from crud import project
from sqlalchemy.orm import Session
from schemas.user import UserBrief, UserDetail
from schemas.milestone import MilestoneDetail
from schemas.task import TaskBrief, SubTaskDetail
from schemas.schedule import ScheduleResponse
from schemas.channel import ChannelResponse, ChannelMemberResponse
from schemas.chat import ChatResponse
from schemas.whiteboard import WhiteBoardDetail

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
        # Convert SQLAlchemy model to dict if needed
        user_obj = m["user"]
        if hasattr(user_obj, "__dict__"):
            user_data = user_obj.__dict__.copy()
            # Remove SQLAlchemy instance state
            user_data.pop('_sa_instance_state', None)
            # Remove notification related fields
            user_data.pop('notification', None)
            user_data.pop('notifications', None)
            user_data.pop('received_notifications', None)
            user_data.pop('sent_notifications', None)
            # Convert to UserDetail
            user_detail = UserDetail.model_validate(user_data, from_attributes=True)
        else:
            # If it's already a dict
            user_data = dict(user_obj)
            # Remove notification related fields
            user_data.pop('notification', None)
            user_data.pop('notifications', None)
            user_data.pop('received_notifications', None)
            user_data.pop('sent_notifications', None)
            user_detail = UserDetail.model_validate(user_data, from_attributes=True)
            
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
    from schemas.task import TaskDetail
    tasks = []
    if db_project.tasks:
        for task in db_project.tasks:
            # 태스크 기본 정보 추출
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "start_date": task.start_date,
                "due_date": task.due_date,
                "completed_at": task.completed_at,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "project_id": task.project_id,
                "milestone_id": task.milestone_id,
                "subtasks": []
            }
            
            # 마일스톤 정보 추가
            if task.milestone:
                from schemas.task import MilestoneBrief
                task_data["milestone"] = MilestoneBrief.model_validate(task.milestone, from_attributes=True)
            
            # 담당자 정보 추가
            assignees = []
            if task.assignees:
                for assignee in task.assignees:
                    assignees.append(UserBrief.model_validate(assignee, from_attributes=True))
            task_data["assignees"] = assignees
            
            # 생성자 정보 추가
            if task.creator:
                task_data["creator"] = UserBrief.model_validate(task.creator, from_attributes=True)
            
            # 하위 업무 정보 추가
            if task.subtasks:
                for subtask in task.subtasks:
                    task_data["subtasks"].append(SubTaskDetail.model_validate(subtask, from_attributes=True))
            
            # 댓글 정보 추가
            comments = []
            if task.comments:
                from schemas.task import CommentDetail
                for comment in task.comments:
                    comments.append(CommentDetail.model_validate(comment, from_attributes=True))
            task_data["comments"] = comments
            
            tasks.append(TaskDetail(**task_data))
            
    project_detail.tasks = tasks
    
    
    milestones = []
    if db_project.milestones:
        for milestone in db_project.milestones:
            milestone_data = {
                "id": milestone.id,
                "title": milestone.title,
                "description": milestone.description,
                "status": milestone.status,
                "priority": milestone.priority,
                "start_date": milestone.start_date,
                "due_date": milestone.due_date,
                "completed_at": milestone.completed_at,
                "progress": milestone.progress,
                "created_at": milestone.created_at,
                "updated_at": milestone.updated_at,
                "project_id": milestone.project_id,
                "tags": milestone.tags
            }
            
            # 담당자 정보 추가
            assignees = []  
            if milestone.assignees:
                for assignee in milestone.assignees:
                    assignees.append(UserBrief.model_validate(assignee, from_attributes=True))
            milestone_data["assignees"] = assignees
            
            # 생성자 정보 추가
            if milestone.creator:
                milestone_data["creator"] = UserBrief.model_validate(milestone.creator, from_attributes=True)
            
            # 태스크 정보 추가
            tasks = []
            if milestone.tasks:
                for task in milestone.tasks:
                    tasks.append(TaskBrief.model_validate(task, from_attributes=True))
            milestone_data["tasks"] = tasks
            
            milestone_data["task_count"] = len(tasks)
            milestone_data["completed_task_count"] = len([t for t in tasks if t.status == "completed"])
            
            milestones.append(MilestoneDetail(**milestone_data))
    project_detail.milestones = milestones
    
    # 참여 요청 정보 추가
    participation_requests = []
    if db_project.participation_requests:
        from schemas.participation_request import ParticipationRequestResponse
        for req in db_project.participation_requests:
            participation_requests.append(
                ParticipationRequestResponse(
                    id=req.id,
                    project_id=req.project_id,
                    sender_id=req.sender_id,
                    receiver_id=req.receiver_id,
                    message=req.message,
                    request_type=req.request_type,
                    status=req.status,
                    created_at=req.created_at,
                    processed_at=req.processed_at,
                    sender=UserBrief.model_validate(req.sender, from_attributes=True),
                    receiver=UserBrief.model_validate(req.receiver, from_attributes=True)
                )
            )
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
            members = []  
            if channel.members:
                for member in channel.members:
                    members.append(ChannelMemberResponse(
                        id=member.id,
                        name=member.name,
                        email=member.email,
                        profile_image=member.profile_image,
                        role="member",  # 기본값, 실제 역할 정보가 있다면 사용
                        joined_at=channel.created_at  # 기본값, 실제 가입 시간이 있다면 사용
                    ))
            
            # ChannelWithMembers 객체 생성
            channel_with_members = ChannelResponse(
                name=channel.name,
                description=channel.description,
                is_public=channel.is_public,
                project_id=channel.project_id,
                channel_id=channel.channel_id,
                created_at=channel.created_at,
                updated_at=channel.updated_at,
                created_by=channel.created_by,
                updated_by=channel.updated_by,
                member_count=len(members),
                chats=[],  # 채팅 정보가 필요하다면 추가
                members=members
            )
            channels.append(channel_with_members)
            
            chats = []
            if channel.chats:
                for chat in channel.chats:
                    chats.append(ChatResponse.model_validate(chat, from_attributes=True))
            channel_with_members.chats = chats
            channel_with_members.chats_count = len(chats)
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