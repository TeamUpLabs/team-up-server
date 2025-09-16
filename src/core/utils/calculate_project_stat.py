from api.v1.models.project.project import Project
from datetime import datetime
from typing import Dict, Any

def calculate_project_stat(project: Project) -> Dict[str, Any]:
  total_tasks = len(project.tasks) if hasattr(project, 'tasks') else 0
  completed_tasks = sum(1 for task in project.tasks if task.status == 'completed') if hasattr(project, 'tasks') else 0
  total_milestones = len(project.milestones) if hasattr(project, 'milestones') else 0
  completed_milestones = sum(1 for milestone in project.milestones if milestone.status == 'completed') if hasattr(project, 'milestones') else 0
  
  progress_percentage = 0
  if total_tasks > 0:
    progress_percentage = round((completed_tasks / total_tasks) * 100, 2)
    
  days_remaining = None
  if project.end_date:
    days_remaining = (project.end_date - datetime.now()).days
  
  return {
    "total_tasks": total_tasks,
    "completed_tasks": completed_tasks,
    "total_milestones": total_milestones,
    "completed_milestones": completed_milestones,
    "progress_percentage": progress_percentage,
    "days_remaining": days_remaining
  }