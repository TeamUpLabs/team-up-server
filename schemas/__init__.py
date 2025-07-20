# 스키마 모듈 초기화 파일
# 순환 참조 문제를 해결하기 위해 import 후 update_forward_refs()를 호출

from schemas.user import UserBase, UserCreate, UserUpdate, UserBrief, UserDetail, Token
from schemas.project import (
    ProjectBase, ProjectCreate, ProjectUpdate, ProjectMember, 
    ProjectBrief, ProjectDetail
)
from schemas.task import (
    TaskBase, TaskCreate, TaskUpdate, TaskBrief, TaskDetail, 
    MilestoneBrief as TaskMilestoneBrief
)
from schemas.milestone import (
    MilestoneBase, MilestoneCreate, MilestoneUpdate, 
    MilestoneBrief, MilestoneDetail
)

from schemas.participation_request import (
    ParticipationRequestBase, ParticipationRequestCreate,
    ParticipationRequestUpdate, ParticipationRequestResponse,
    ParticipationRequestList
)
from schemas.schedule import (
    ScheduleBase, ScheduleCreate, ScheduleUpdate, ScheduleResponse
)
from schemas.notification import (
    NotificationBase, NotificationCreate, NotificationUpdate,
    NotificationResponse, NotificationListResponse
)
from schemas.channel import (
    ChannelBase, ChannelCreate, ChannelUpdate, ChannelResponse,
    ChannelListResponse, ChannelMemberCreate,
    ChannelMemberResponse
)
from schemas.chat import (
    ChatBase, ChatCreate, ChatUpdate, ChatResponse, ChatListResponse,
    ChatSearchRequest, ChatDateRangeRequest, UserInfo
)
from schemas.session import (
    SessionBase, SessionCreate, SessionUpdate, SessionDetail
)

# 순환 참조 해결을 위한 forward refs 업데이트
ProjectDetail.update_forward_refs()
TaskDetail.update_forward_refs()
MilestoneDetail.update_forward_refs() 
ScheduleResponse.update_forward_refs()
