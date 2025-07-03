from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from database import Base

# 프로젝트-멤버 관계 테이블
project_members = Table(
    'project_members',
    Base.metadata,
    Column('project_id', String(6), ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(50), nullable=True),
    Column('is_leader', Integer, default=0, nullable=False),  # 0: 아니오, 1: 예
    Column('is_manager', Integer, default=0, nullable=False),  # 0: 아니오, 1: 예
    Column('joined_at', DateTime, nullable=False, server_default=func.now()),
    Index('idx_project_members', 'project_id', 'user_id')
)

# 업무-담당자 관계 테이블
task_assignees = Table(
    'task_assignees',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime, nullable=False, server_default=func.now()),
    Index('idx_task_assignees', 'task_id', 'user_id')
)

# 마일스톤-담당자 관계 테이블
milestone_assignees = Table(
    'milestone_assignees',
    Base.metadata,
    Column('milestone_id', Integer, ForeignKey('milestones.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime, nullable=False, server_default=func.now()),
    Index('idx_milestone_assignees', 'milestone_id', 'user_id')
)

# 프로젝트-기술 스택 관계 테이블
project_tech_stacks = Table(
    'project_tech_stacks',
    Base.metadata,
    Column('project_id', String(6), ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('tech_stack_id', Integer, ForeignKey('tech_stacks.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_project_tech_stacks', 'project_id', 'tech_stack_id')
) 