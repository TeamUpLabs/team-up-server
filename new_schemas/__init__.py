# 스키마 모듈 초기화 파일
# 순환 참조 문제를 해결하기 위해 import 후 update_forward_refs()를 호출

from new_schemas.user import UserBase, UserCreate, UserUpdate, UserBrief, UserDetail, Token
from new_schemas.project import (
    ProjectBase, ProjectCreate, ProjectUpdate, ProjectMember, 
    ProjectBrief, ProjectDetail, TechStackBase
)
from new_schemas.task import (
    TaskBase, TaskCreate, TaskUpdate, TaskBrief, TaskDetail, 
    MilestoneBrief as TaskMilestoneBrief
)
from new_schemas.milestone import (
    MilestoneBase, MilestoneCreate, MilestoneUpdate, 
    MilestoneBrief, MilestoneDetail
)
from new_schemas.tech_stack import (
    TechStackBase as TechStackBaseSchema, TechStackCreate, 
    TechStackUpdate, TechStackDetail
)
from new_schemas.participation_request import (
    ParticipationRequestBase, ParticipationRequestCreate,
    ParticipationRequestUpdate, ParticipationRequestResponse,
    ParticipationRequestList
)
from new_schemas.schedule import (
    ScheduleBase, ScheduleCreate, ScheduleUpdate, ScheduleResponse
)
from new_schemas.notification import (
    NotificationBase, NotificationCreate, NotificationUpdate,
    NotificationResponse, NotificationListResponse
)

# 순환 참조 해결을 위한 forward refs 업데이트
ProjectDetail.update_forward_refs()
TaskDetail.update_forward_refs()
MilestoneDetail.update_forward_refs() 
ScheduleResponse.update_forward_refs()
