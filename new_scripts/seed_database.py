#!/usr/bin/env python3
"""
이 스크립트는 샘플 데이터를 데이터베이스에 추가합니다.
샘플 데이터는 sample_data.json 파일에서 읽어옵니다.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any
from sqlalchemy import text

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("seed-database")

# 모듈 임포트
from database import SessionLocal, engine, Base
from new_models.user import (
    User, CollaborationPreference, UserInterest, 
    UserSocialLink
)
from new_models.project import Project
from new_models.task import Task, SubTask, Comment
from new_models.milestone import Milestone
from new_models.tech_stack import TechStack
from auth import get_password_hash

def load_sample_data() -> Dict[str, List[Dict[str, Any]]]:
    """sample_data.json에서 샘플 데이터 로드"""
    data_path = project_root / "new_scripts" / "sample_data.json"
    logger.info(f"샘플 데이터 파일 로드: {data_path}")
    
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"샘플 데이터 로드 오류: {e}")
        sys.exit(1)

def create_database_tables():
    """데이터베이스 테이블 생성"""
    logger.info("데이터베이스 테이블 생성")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("테이블 생성 완료")
    except Exception as e:
        logger.error(f"테이블 생성 오류: {e}")
        sys.exit(1)

def seed_users(db, users_data):
    """사용자 데이터 추가"""
    logger.info("사용자 데이터 추가 중...")
    
    for user_data in users_data:
        # 이미 존재하는 사용자 확인
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            logger.info(f"사용자 이미 존재: {user_data['email']}")
            continue
            
        # 비밀번호 해싱
        hashed_password = get_password_hash(user_data["password"])
        
        # 기본 알림 설정
        default_notification_settings = {
            "emailEnable": 1,
            "taskNotification": 1,
            "milestoneNotification": 1,
            "scheduleNotification": 1,
            "deadlineNotification": 1,
            "weeklyReport": 1,
            "pushNotification": 1,
            "securityNotification": 1
        }
        
        # 사용자가 제공한 알림 설정이 있으면 병합
        if "notification_settings" in user_data:
            default_notification_settings.update(user_data["notification_settings"])
        
        # 사용자 생성
        user = User(
            name=user_data["name"],
            email=user_data["email"],
            hashed_password=hashed_password,
            profile_image=user_data.get("profile_image"),
            bio=user_data.get("bio"),
            role=user_data.get("role"),
            status=user_data.get("status", "active"),
            languages=user_data.get("languages"),
            phone=user_data.get("phone"),
            birth_date=user_data.get("birth_date"),
            auth_provider=user_data.get("auth_provider", "local"),
            auth_provider_id=user_data.get("auth_provider_id"),
            notification_settings=default_notification_settings,
        )
        
        db.add(user)
        db.flush()  # ID를 생성하기 위해 flush
        
        # 협업 선호도 추가
        if "collaboration_preferences" in user_data:
            for pref_data in user_data["collaboration_preferences"]:
                pref = CollaborationPreference(
                    user_id=user.id,
                    preference_type=pref_data["preference_type"],
                    preference_value=pref_data["preference_value"]
                )
                db.add(pref)
        
        # 관심분야 추가
        if "interests" in user_data:
            for interest_data in user_data["interests"]:
                interest = UserInterest(
                    user_id=user.id,
                    interest_category=interest_data["interest_category"],
                    interest_name=interest_data["interest_name"]
                )
                db.add(interest)
        
        # 소셜 링크 추가
        if "social_links" in user_data:
            for link_data in user_data["social_links"]:
                link = UserSocialLink(
                    user_id=user.id,
                    platform=link_data["platform"],
                    url=link_data["url"]
                )
                db.add(link)
        
        logger.info(f"사용자 추가: {user_data['email']}")
    
    db.commit()
    logger.info(f"사용자 데이터 추가 완료: {len(users_data)}명")

def seed_tech_stacks(db, tech_stacks_data):
    """기술 스택 데이터 추가"""
    logger.info("기술 스택 데이터 추가 중...")
    
    for tech_data in tech_stacks_data:
        # 이미 존재하는 기술 스택 확인
        existing_tech = db.query(TechStack).filter(TechStack.name == tech_data["name"]).first()
        if existing_tech:
            logger.info(f"기술 스택 이미 존재: {tech_data['name']}")
            continue
            
        # 기술 스택 생성
        tech = TechStack(
            name=tech_data["name"],
            category=tech_data.get("category"),
            icon_url=tech_data.get("icon_url"),
        )
        
        db.add(tech)
        logger.info(f"기술 스택 추가: {tech_data['name']}")
    
    db.commit()
    logger.info(f"기술 스택 데이터 추가 완료: {len(tech_stacks_data)}개")

def seed_user_tech_stacks(db, user_tech_stacks_data):
    """사용자 기술 스택 관계 데이터 추가"""
    logger.info("사용자 기술 스택 관계 데이터 추가 중...")
    
    for uts_data in user_tech_stacks_data:
        # 이미 존재하는 관계 확인
        existing_uts = db.execute(
            text("""
            SELECT * FROM user_tech_stacks 
            WHERE user_id = :user_id AND tech_stack_id = :tech_stack_id
            """),
            {"user_id": uts_data["user_id"], "tech_stack_id": uts_data["tech_stack_id"]}
        ).fetchone()
        
        if existing_uts:
            logger.info(f"사용자 기술 스택 관계 이미 존재: user_id={uts_data['user_id']}, tech_stack_id={uts_data['tech_stack_id']}")
            continue
        
        # 사용자 기술 스택 관계 추가
        db.execute(
            text("""
            INSERT INTO user_tech_stacks 
            (user_id, tech_stack_id, proficiency_level, years_experience) 
            VALUES (:user_id, :tech_stack_id, :proficiency_level, :years_experience)
            """),
            {
                "user_id": uts_data["user_id"],
                "tech_stack_id": uts_data["tech_stack_id"],
                "proficiency_level": uts_data.get("proficiency_level"),
                "years_experience": uts_data.get("years_experience")
            }
        )
        logger.info(f"사용자 기술 스택 관계 추가: user_id={uts_data['user_id']}, tech_stack_id={uts_data['tech_stack_id']}")
    
    db.commit()
    logger.info(f"사용자 기술 스택 관계 데이터 추가 완료: {len(user_tech_stacks_data)}개")

def seed_projects(db, projects_data):
    """프로젝트 데이터 추가"""
    logger.info("프로젝트 데이터 추가 중...")
    
    for project_data in projects_data:
        # 이미 존재하는 프로젝트 확인
        existing_project = db.query(Project).filter(Project.id == project_data["id"]).first()
        if existing_project:
            logger.info(f"프로젝트 이미 존재: {project_data['id']}")
            continue
            
        # 기본 데이터 준비
        project_dict = {
            "id": project_data["id"],
            "title": project_data["title"],
            "description": project_data["description"],
            "status": project_data.get("status", "planning"),
            "visibility": project_data.get("visibility", "public"),
            "owner_id": project_data["owner_id"],
            "tags": project_data.get("tags"),
            "project_type": project_data.get("project_type"),
            "location": project_data.get("location"),
            "github_url": project_data.get("github_url"),
            "created_at": project_data.get("created_at"),
            "updated_at": project_data.get("updated_at")
        }
        
        # 날짜 필드 처리
        if "created_at" in project_data:
            project_dict["created_at"] = datetime.fromisoformat(project_data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in project_data:
            project_dict["updated_at"] = datetime.fromisoformat(project_data["updated_at"].replace("Z", "+00:00"))
        if "start_date" in project_data:
            project_dict["start_date"] = datetime.fromisoformat(project_data["start_date"].replace("Z", "+00:00"))
        if "end_date" in project_data:
            project_dict["end_date"] = datetime.fromisoformat(project_data["end_date"].replace("Z", "+00:00"))
        if "completed_at" in project_data:
            project_dict["completed_at"] = datetime.fromisoformat(project_data["completed_at"].replace("Z", "+00:00"))
        
        # 프로젝트 생성
        project = Project(**project_dict)
        
        # 기술 스택 연결
        if "tech_stack_ids" in project_data:
            tech_stacks = db.query(TechStack).filter(TechStack.id.in_(project_data["tech_stack_ids"])).all()
            project.tech_stacks = tech_stacks
            
        # 멤버 추가
        if "member_ids" in project_data:
            members = db.query(User).filter(User.id.in_(project_data["member_ids"])).all()
            project.members = members
            
        db.add(project)
        db.flush()  # ID를 생성하기 위해 flush
        
        # 멤버 권한 설정 (소유자는 리더 및 관리자로 설정)
        from new_models.association_tables import project_members
        from sqlalchemy import update
        
        # 소유자를 리더 및 관리자로 설정
        db.execute(
            update(project_members).where(
                project_members.c.project_id == project.id,
                project_members.c.user_id == project.owner_id
            ).values(
                is_leader=1,
                role="owner"
            )
        )
        
        # 멤버 역할 및 권한 설정 (예: 첫 번째 멤버를 관리자로 설정)
        if "member_ids" in project_data and len(project_data["member_ids"]) > 1:
            # 소유자를 제외한 첫 번째 멤버를 관리자로 설정
            for member_id in project_data["member_ids"]:
                if member_id != project.owner_id:
                    db.execute(
                        update(project_members).where(
                            project_members.c.project_id == project.id,
                            project_members.c.user_id == member_id
                        ).values(
                            is_manager=1,
                            role="manager"
                        )
                    )
                    break  # 한 명만 관리자로 설정
            
        logger.info(f"프로젝트 추가: {project_data['id']} - {project_data['title']}")
    
    db.commit()
    logger.info(f"프로젝트 데이터 추가 완료: {len(projects_data)}개")

def seed_milestones(db, milestones_data):
    """마일스톤 데이터 추가"""
    logger.info("마일스톤 데이터 추가 중...")
    
    for milestone_data in milestones_data:
        # 기본 데이터 준비
        milestone_dict = {
            "title": milestone_data["title"],
            "description": milestone_data.get("description"),
            "status": milestone_data.get("status", "not_started"),
            "priority": milestone_data.get("priority", "medium"),
            "project_id": milestone_data["project_id"],
            "created_by": milestone_data.get("created_by"),
            "tags": milestone_data.get("tags"),
        }
        
        # 날짜 필드 처리
        if "start_date" in milestone_data:
            milestone_dict["start_date"] = datetime.fromisoformat(milestone_data["start_date"].replace("Z", "+00:00"))
        if "due_date" in milestone_data:
            milestone_dict["due_date"] = datetime.fromisoformat(milestone_data["due_date"].replace("Z", "+00:00"))
        if "completed_at" in milestone_data:
            milestone_dict["completed_at"] = datetime.fromisoformat(milestone_data["completed_at"].replace("Z", "+00:00"))
        
        # 마일스톤 생성
        milestone = Milestone(**milestone_dict)
        
        # 담당자 추가
        if "assignee_ids" in milestone_data:
            assignees = db.query(User).filter(User.id.in_(milestone_data["assignee_ids"])).all()
            milestone.assignees = assignees
            
        db.add(milestone)
        logger.info(f"마일스톤 추가: {milestone_data['title']}")
    
    db.commit()
    logger.info(f"마일스톤 데이터 추가 완료: {len(milestones_data)}개")

def seed_tasks(db, tasks_data):
    """업무 데이터 추가"""
    logger.info("업무 데이터 추가 중...")
    
    for task_data in tasks_data:
        # 기본 데이터 준비
        task_dict = {
            "title": task_data["title"],
            "description": task_data.get("description"),
            "status": task_data.get("status", "not_started"),
            "priority": task_data.get("priority", "medium"),
            "estimated_hours": task_data.get("estimated_hours"),
            "actual_hours": task_data.get("actual_hours"),
            "project_id": task_data["project_id"],
            "milestone_id": task_data.get("milestone_id"),
            "created_by": task_data.get("created_by"),
        }
        
        # 날짜 필드 처리
        if "start_date" in task_data:
            task_dict["start_date"] = datetime.fromisoformat(task_data["start_date"].replace("Z", "+00:00"))
        if "due_date" in task_data:
            task_dict["due_date"] = datetime.fromisoformat(task_data["due_date"].replace("Z", "+00:00"))
        if "completed_at" in task_data:
            task_dict["completed_at"] = datetime.fromisoformat(task_data["completed_at"].replace("Z", "+00:00"))
        
        # 업무 생성
        task = Task(**task_dict)
        
        # 담당자 추가
        if "assignee_ids" in task_data:
            assignees = db.query(User).filter(User.id.in_(task_data["assignee_ids"])).all()
            task.assignees = assignees
        
        db.add(task)
        db.flush()  # ID를 생성하기 위해 flush
        
        # 하위 업무 추가
        if "subtasks" in task_data:
            for subtask_data in task_data["subtasks"]:
                subtask = SubTask(
                    title=subtask_data["title"],
                    task_id=task.id,
                    is_completed=subtask_data.get("is_completed", False),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(subtask)
                logger.info(f"하위 업무 추가: {subtask_data['title']}")
            
        logger.info(f"업무 추가: {task_data['title']}")
    
    db.commit()
    logger.info(f"업무 데이터 추가 완료: {len(tasks_data)}개")

def seed_comments(db, tasks_data):
    """댓글 데이터 추가"""
    logger.info("댓글 데이터 추가 중...")
    
    for task_data in tasks_data:
        if "comments" not in task_data:
            continue
            
        # 해당 업무 찾기
        task = db.query(Task).filter(Task.title == task_data["title"]).first()
        if not task:
            logger.warning(f"업무를 찾을 수 없음: {task_data['title']}")
            continue
        
        for comment_data in task_data["comments"]:
            # 이미 존재하는 댓글 확인 (내용과 작성자로)
            existing_comment = db.query(Comment).filter(
                Comment.content == comment_data["content"],
                Comment.created_by == comment_data["created_by"],
                Comment.task_id == task.id
            ).first()
            
            if existing_comment:
                logger.info(f"댓글 이미 존재: {comment_data['content'][:20]}...")
                continue
            
            # 댓글 생성
            comment = Comment(
                content=comment_data["content"],
                task_id=task.id,
                created_by=comment_data["created_by"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(comment)
            logger.info(f"댓글 추가: {comment_data['content'][:20]}...")
    
    db.commit()
    logger.info("댓글 데이터 추가 완료")

def seed_database():
    """데이터베이스에 샘플 데이터 추가"""
    logger.info("데이터베이스 시드 작업 시작")
    
    # 샘플 데이터 로드
    data = load_sample_data()
    
    # 데이터베이스 세션 생성
    db = SessionLocal()
    
    try:
        # 데이터베이스 테이블 생성
        create_database_tables()
        
        # 데이터 추가 (순서 중요: 외래키 의존성 고려)
        seed_users(db, data.get("users", []))
        seed_tech_stacks(db, data.get("tech_stacks", []))
        seed_user_tech_stacks(db, data.get("user_tech_stacks", []))
        seed_projects(db, data.get("projects", []))
        seed_milestones(db, data.get("milestones", []))
        seed_tasks(db, data.get("tasks", []))
        seed_comments(db, data.get("tasks", []))
        
        logger.info("데이터베이스 시드 작업 완료")
    except Exception as e:
        db.rollback()
        logger.error(f"데이터베이스 시드 작업 중 오류 발생: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 