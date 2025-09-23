from api.v1.repositories.project.task_repository import TaskRepository
from api.v1.schemas.project.task_schema import CommentCreate, CommentUpdate, SubTaskCreate, TaskCreate, TaskUpdate
from api.v1.models.project.task import SubTask, Task, Comment
from sqlalchemy.orm import Session
from typing import List
from api.v1.schemas.project.task_schema import TaskDetail, CommentDetail

class TaskService:
  def __init__(self, db: Session):
    self.repository = TaskRepository(db)
    
  def get(self, project_id: str, task_id: int) -> TaskDetail:
    return self.repository.get(project_id, task_id)
  
  def get_all_tasks_by_project_id(self, project_id: str) -> List[TaskDetail]:
    return self.repository.get_all_tasks_by_project_id(project_id)
    
  def get_all_tasks_by_milestone_id(self, project_id: str, milestone_id: int) -> List[TaskDetail]:
    return self.repository.get_all_tasks_by_milestone_id(project_id, milestone_id)
    
  def get_all_tasks_by_assignee_id(self, project_id: str, assignee_id: int) -> List[TaskDetail]:
    return self.repository.get_all_tasks_by_assignee_id(project_id, assignee_id)
    
  def create(self, project_id: str, task: TaskCreate) -> Task:
    return self.repository.create(project_id, task)
    
  def update(self, project_id: str, task_id: int, task: TaskUpdate) -> Task:
    return self.repository.update(project_id, task_id, task)
    
  def delete(self, project_id: str, task_id: int) -> bool:
    return self.repository.delete(project_id, task_id)
    
  def add_assignee(self, project_id: str, task_id: int, user_id: int) -> Task:
    return self.repository.add_assignee(project_id, task_id, user_id)
    
  def remove_assignee(self, project_id: str, task_id: int, user_id: int) -> Task:
    return self.repository.remove_assignee(project_id, task_id, user_id)
    
  def is_manager(self, project_id: str, task_id: int, user_id: int) -> bool:
    return self.repository.is_manager(project_id, task_id, user_id)
  
  def add_subtask(self, project_id: str, task_id: int, user_id: int, subtask: SubTaskCreate) -> SubTask:
    return self.repository.add_subtask(project_id, task_id, user_id, subtask)
  
  def get_comments(self, project_id: str, task_id: int) -> List[CommentDetail]:
    return self.repository.get_comments(project_id, task_id)
    
  def add_comment(self, project_id: str, task_id: int, comment: CommentCreate) -> Comment:
    return self.repository.create_comment(project_id, task_id, comment)
  
  def update_comment(self, project_id: str, task_id: int, comment_id: int, comment: CommentUpdate) -> Comment:
    return self.repository.update_comment(project_id, task_id, comment_id, comment)
    
  def remove_comment(self, project_id: str, task_id: int, comment_id: int) -> Comment:
    return self.repository.delete_comment(project_id, task_id, comment_id)
    