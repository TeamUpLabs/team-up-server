from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime, Index, func
from core.database.database import Base

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

# 스케줄-담당자 관계 테이블
schedule_assignees = Table(
  'schedule_assignees',
  Base.metadata,
  Column('schedule_id', Integer, ForeignKey('schedules.id', ondelete='CASCADE'), primary_key=True),
  Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
  Column('assigned_at', DateTime, nullable=False, server_default=func.now()),
  Index('idx_schedule_assignees', 'schedule_id', 'user_id')
)

# 사용자-관심분야 관계 테이블
user_interests = Table(
  'user_interests',
  Base.metadata,
  Column('id', Integer, primary_key=True),
  Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
  Column('interest_category', String(50), nullable=False),
  Column('interest_name', String(100), nullable=False),
  Column('created_at', DateTime, nullable=False, server_default=func.now()),
  Index('idx_user_interests', 'user_id')
)

# 사용자-소셜링크 관계 테이블
user_social_links = Table(
  'user_social_links',
  Base.metadata,
  Column('id', Integer, primary_key=True),
  Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
  Column('platform', String(50), nullable=False),  # github, linkedin, twitter 등
  Column('url', String(255), nullable=False),
  Column('created_at', DateTime, nullable=False, server_default=func.now()),
  Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
  Index('idx_user_social_links', 'user_id')
)

# 채널-멤버 관계 테이블
channel_members = Table(
  'channel_members',
  Base.metadata,
  Column('channel_id', String, ForeignKey('channels.channel_id', ondelete='CASCADE'), primary_key=True),
  Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
  Column('joined_at', DateTime, nullable=False, server_default=func.now()),
  Column('role', String(50), default='member'),  # member, admin, moderator 등
  Index('idx_channel_members', 'channel_id', 'user_id')
)

# 사용자-화이트보드 좋아요 관계 테이블
user_whiteboard_likes = Table(
  'user_whiteboard_likes',
  Base.metadata,
  Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
  Column('whiteboard_id', Integer, ForeignKey('whiteboards.id', ondelete='CASCADE'), primary_key=True),
  Column('created_at', DateTime, nullable=False, server_default=func.now()),
  Index('idx_user_whiteboard_likes', 'user_id', 'whiteboard_id')
)

# 사용자-사용자 팔로우 관계 테이블
user_follows = Table(
    'user_follows',
    Base.metadata,
    Column('follower_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('followed_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
    Index('idx_user_follows', 'follower_id', 'followed_id')
)

# 사용자-게시물 북마크 관계 테이블
user_post_bookmarks = Table(
    'user_post_bookmarks',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
    Index('idx_user_post_bookmarks', 'user_id', 'post_id')
)

# 멘토-멘티 관계 테이블 (User-User 관계)
mentor_mentees = Table(
    'mentor_mentees',
    Base.metadata,
    Column('mentor_user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('mentee_user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
    Column('status', String(50), default='active', nullable=False),  # active, inactive, completed
    Index('idx_mentor_mentees', 'mentor_user_id', 'mentee_user_id')
)

