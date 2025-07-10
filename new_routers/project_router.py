from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from new_crud import project
from new_models.user import User
from new_models.project import Project
from new_schemas.project import ProjectCreate, ProjectUpdate, ProjectDetail, ProjectBrief, ProjectMember
from new_schemas.user import UserBrief, UserDetail
from new_schemas.milestone import MilestoneDetail
from new_schemas.task import TaskBrief, SubTaskDetail
from new_schemas.schedule import ScheduleResponse
from new_schemas.channel import ChannelResponse, ChannelMemberResponse
from new_schemas.chat import ChatResponse
from utils.sse_manager import project_sse_manager
import json

router = APIRouter(
    prefix="/api/projects",
    tags=["projects"]
)

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
    project_detail.members = [
        ProjectMember(
            user=UserDetail.model_validate(m["user"], from_attributes=True),
            role=m["role"],
            is_leader=m["is_leader"],
            is_manager=m["is_manager"],
            joined_at=m["joined_at"]
        )
        for m in member_info
    ]
    
    # 태스크 정보 추가
    from new_schemas.task import TaskDetail
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
                from new_schemas.task import MilestoneBrief
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
                from new_schemas.task import CommentDetail
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
        from new_schemas.participation_request import ParticipationRequestResponse
        for req in db_project.participation_requests:
            participation_requests.append(
                ParticipationRequestResponse(
                    id=req.id,
                    project_id=req.project_id,
                    user_id=req.user_id,
                    message=req.message,
                    request_type=req.request_type,
                    status=req.status,
                    created_at=req.created_at,
                    processed_at=req.processed_at,
                    user=UserBrief.model_validate(req.user, from_attributes=True)
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
                        user_id=member.id,
                        name=member.name,
                        email=member.email,
                        profile_image=member.profile_image,
                        role="member",  # 기본값, 실제 역할 정보가 있다면 사용
                        joined_at=channel.created_at  # 기본값, 실제 가입 시간이 있다면 사용
                    ))
            
            # ChannelWithMembers 객체 생성
            channel_with_members = ChannelResponse(
                id=channel.id,
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
    
    # 통계 정보 추가
    project_detail.task_count = len(db_project.tasks)
    project_detail.completed_task_count = len([t for t in db_project.tasks if t.status == "completed"])
    project_detail.milestone_count = len(db_project.milestones)
    project_detail.participation_request_count = len(db_project.participation_requests)
    project_detail.schedule_count = len(db_project.schedules)
    project_detail.channel_count = len(db_project.channels)
    project_detail.chat_count = len([chat for channel in db_project.channels for chat in channel.chats])
    
    return project_detail

@router.post("/", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
async def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """새 프로젝트 생성"""
    # 현재 사용자가 소유자인지 확인
    if project_in.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 소유로 프로젝트를 생성할 수 없습니다."
        )
    db_project = project.create(db=db, obj_in=project_in)
    if db_project:
        project_detail = convert_project_to_project_detail(db_project, db)
        await project_sse_manager.send_event(
            db_project.id,
            json.dumps(project_sse_manager.convert_to_dict(project_detail))
        )
    return project_detail

@router.get("/", response_model=List[ProjectBrief])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """프로젝트 목록 조회"""
    projects = project.get_multi(db=db, skip=skip, limit=limit)
    return [ProjectBrief.model_validate(p, from_attributes=True) for p in projects]

@router.get("/ids", response_model=List[str])
def get_all_project_ids(db: Session = Depends(get_db)):
    """모든 프로젝트 ID 조회"""
    project_ids = project.get_all_project_ids(db=db)
    return project_ids

@router.get("/{project_id}", response_model=ProjectDetail)
def read_project(project_id: str, db: Session = Depends(get_db)):
    """특정 프로젝트 정보 조회"""
    db_project = project.get(db=db, id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    return convert_project_to_project_detail(db_project, db)

@router.put("/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: str, 
    project_in: ProjectUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """프로젝트 정보 수정"""
    db_project = project.get(db=db, id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    # 소유자 또는 관리자만 수정 가능
    if db_project.owner_id != current_user.id and not project.is_manager(db=db, project_id=project_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 프로젝트를 수정할 권한이 없습니다."
        )
    
    db_project = project.update(db=db, db_obj=db_project, obj_in=project_in)
    if db_project:
        project_detail = convert_project_to_project_detail(db_project, db)
        await project_sse_manager.send_event(
            db_project.id,
            json.dumps(project_sse_manager.convert_to_dict(project_detail))
        )
        return project_detail
    return None

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """프로젝트 삭제"""
    db_project = project.get(db=db, id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    # 소유자만 삭제 가능
    if db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 프로젝트를 삭제할 권한이 없습니다."
        )
    
    project.remove(db=db, id=project_id)
    # 204 응답은 본문을 포함해서는 안됨
    return None

@router.get("/{project_id}/members", response_model=List[ProjectMember])
def read_project_members(project_id: str, db: Session = Depends(get_db)):
    """프로젝트 멤버 목록 조회"""
    member_info = project.get_project_members(db=db, project_id=project_id)
    return [
        ProjectMember(
            user=UserDetail.model_validate(m["user"], from_attributes=True),
            role=m["role"],
            is_leader=m["is_leader"],
            is_manager=m["is_manager"],
            joined_at=m["joined_at"]
        )
        for m in member_info
    ]

@router.get("/{project_id}/milestones", response_model=List)
def read_project_milestones(project_id: str, db: Session = Depends(get_db)):
    """프로젝트 마일스톤 목록 조회"""
    from new_schemas.milestone import MilestoneBrief
    milestones = project.get_milestones(db=db, project_id=project_id)
    return [MilestoneBrief.model_validate(m, from_attributes=True) for m in milestones]

@router.get("/{project_id}/tasks", response_model=List)
def read_project_tasks(project_id: str, db: Session = Depends(get_db)):
    """프로젝트 업무 목록 조회"""
    from new_schemas.task import TaskBrief
    tasks = project.get_tasks(db=db, project_id=project_id)
    return [TaskBrief.model_validate(t, from_attributes=True) for t in tasks] 

@router.get("/exclude/{member_id}", response_model=List[ProjectDetail])
def get_projects_excluding_my_project(member_id: int, db: Session = Depends(get_db)):
    """내가 속한 프로젝트를 제외한 모든 프로젝트 조회"""
    other_projects = project.get_all_project_excluding_me(db=db, member_id=member_id)
    return [convert_project_to_project_detail(p, db) for p in other_projects]

@router.put("/{project_id}/member/{member_id}")
async def update_project_member_permission(project_id: str, member_id: int, permission: str, db: Session = Depends(get_db)):
    """프로젝트 멤버 권한 수정 (leader, manager, member)"""
    """/api/projects/{project_id}/member/{member_id}?permission=manager"""
    db_project = project.update_project_member_permission(db=db, project_id=project_id, member_id=member_id, permission=permission)
    project_detail = convert_project_to_project_detail(db_project, db)
    await project_sse_manager.send_event(
        db_project.id,
        json.dumps(project_sse_manager.convert_to_dict(project_detail))
    )
    return project_detail

@router.post("/{project_id}/member/{member_id}")
async def add_member_to_project(project_id: str, member_id: int, db: Session = Depends(get_db)):
    """프로젝트 멤버 추가"""
    db_project = project.add_member(db=db, project_id=project_id, member_id=member_id)
    project_detail = convert_project_to_project_detail(db_project, db)
    await project_sse_manager.send_event(
        db_project.id,
        json.dumps(project_sse_manager.convert_to_dict(project_detail))
    )
    return project_detail

@router.put("/{project_id}/member/{member_id}/kick")
async def kick_out_member_from_project(project_id: str, member_id: int, db: Session = Depends(get_db)):
    """프로젝트 멤버 추방"""
    db_project = project.remove_member(db=db, project_id=project_id, member_id=member_id)
    project_detail = convert_project_to_project_detail(db_project, db)
    await project_sse_manager.send_event(
        db_project.id,
        json.dumps(project_sse_manager.convert_to_dict(project_detail))
    )
    return project_detail

@router.get("/{project_id}/sse")
async def read_project_sse(project_id: str, request: Request, db: Session = Depends(get_db)):
    """프로젝트 SSE 연결"""
    queue = await project_sse_manager.connect(project_id)
    
    async def event_generator():
        try:
            db_project = project.get(db, project_id)
            project_detail = convert_project_to_project_detail(db_project, db)
            if project_detail:
                project_dict = project_sse_manager.convert_to_dict(project_detail)
                yield f"data: {json.dumps(project_dict)}\n\n"
        finally:
            db.close()
            
        async for event in project_sse_manager.event_generator(project_id, queue):
            if await request.is_disconnected():
                await project_sse_manager.disconnect(project_id, queue)
                break
            yield event
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"  # Add CORS header
        }
    )
