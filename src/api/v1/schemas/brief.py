from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, model_validator

class UserBrief(BaseModel):
  """간략한 사용자 정보"""
  id: int
  name: str
  email: str
  profile_image: Optional[str] = None
  job: Optional[str] = None
  status: Optional[str] = None
  created_at: datetime
  updated_at: datetime
  
  links: Dict[str, Any] = {}
  
  def model_post_init(self, __context):
    self.links = {
      "self": {
        "href": f"/api/v1/users/{self.id}",
        "method": "GET",
        "title": "사용자 정보 조회"
      }
    }
    
  class Config:
    from_attributes = True
  

class ProjectBrief(BaseModel):
  """간략한 프로젝트 정보"""
  id: str
  title: str
  description: Optional[str] = None
  status: str
  team_size: int
  tags: Optional[List[str]] = None
  members: Optional[List[UserBrief]] = None
  project_type: Optional[str] = None
  links: Dict[str, Any] = {}
  
  def model_post_init(self, __context):
    self.links = {
      "self": {
        "href": f"/api/v1/projects/{self.id}",
        "method": "GET",
        "title": "프로젝트 정보 조회"
      }
    }
  
  class Config:
    from_attributes = True
    
class TaskBrief(BaseModel):
  """간략한 업무 정보"""
  id: int
  title: str
  status: str
  priority: str
  due_date: Optional[datetime] = None
  links: Dict[str, Any] = {}
  
  def model_post_init(self, __context):
    self.links = {
      "self": {
        "href": f"/api/v1/tasks/{self.id}",
        "method": "GET",
        "title": "업무 정보 조회"
      },
      "put": {
        "href": f"/api/v1/tasks/{self.id}",
        "method": "PUT",
        "title": "업무 정보 수정"
      },
      "delete": {
        "href": f"/api/v1/tasks/{self.id}",
        "method": "DELETE",
        "title": "업무 정보 삭제"
      }
    }
  
  class Config:
    from_attributes = True
  
class MilestoneBrief(BaseModel):
  """간략한 마일스톤 정보"""
  id: int
  title: str
  status: str
  due_date: Optional[datetime] = None
  links: Dict[str, Any] = {}
  
  def model_post_init(self, __context):
    self.links = {
      "self": {
        "href": f"/api/v1/milestones/{self.id}",
        "method": "GET",
        "title": "마일스톤 정보 조회"
      },
      "put": {
        "href": f"/api/v1/milestones/{self.id}",
        "method": "PUT",
        "title": "마일스톤 정보 수정"
      },
      "delete": {
        "href": f"/api/v1/milestones/{self.id}",
        "method": "DELETE",
        "title": "마일스톤 정보 삭제"
      }
    }
  
  class Config:
    from_attributes = True
    
class WhiteBoardBrief(BaseModel):
    id: int
    type: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserBrief] = None
    updater: Optional[UserBrief] = None
    
    links: Dict[str, Any] = {}
    
    def model_post_init(self, __context):
      self.links = {
        "self": {
          "href": f"/api/v1/whiteboards/{self.id}",
          "method": "GET",
          "title": "화이트보드 정보 조회"
        },
        "post": {
          "href": f"/api/v1/whiteboards/{self.id}",
          "method": "POST",
          "title": "화이트보드 생성"
        },
        "put": {
          "href": f"/api/v1/whiteboards/{self.id}",
          "method": "PUT",
          "title": "화이트보드 정보 수정"
        },
        "delete": {
          "href": f"/api/v1/whiteboards/{self.id}",
          "method": "DELETE",
          "title": "화이트보드 정보 삭제"
        }
      }
    
    class Config:
        from_attributes = True