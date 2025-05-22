from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any
import json

class ScheduleBase(BaseModel):
    project_id: str
    type: str
    title: str
    description: str
    where: str
    start_time: str
    end_time: str
    status: str
    created_at: str
    updated_at: str
    created_by: int
    updated_by: int

    model_config = ConfigDict(from_attributes=True)

class ScheduleCreate(ScheduleBase):
    assignee_id: List[int] = []

    @field_validator('assignee_id', mode='before')
    @classmethod
    def prepare_assignee_id(cls, v: Any) -> List[int]:
        if v is None:
            return []  # Default to empty list if None is explicitly passed
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            if not v.strip(): # Handle empty string case
                return []
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [int(item) for item in data]
                elif isinstance(data, int):
                    return [data]
                else:
                    raise ValueError("assignee_id string must represent an integer or a list of integers")
            except json.JSONDecodeError:
                try:
                    return [int(v)]
                except ValueError:
                    raise ValueError("assignee_id string is not a valid integer or JSON list/integer")
            except (ValueError, TypeError):
                 raise ValueError("assignee_id list contains non-integer values")

        if isinstance(v, list):
            if not v: # Handles empty list []
                return []
            try:
                return [int(item) for item in v]
            except (ValueError, TypeError):
                raise ValueError("All items in assignee_id list must be integers")
        
        raise ValueError(f"Unsupported type for assignee_id: {type(v)}. Expected int, str, or list.")

    model_config = ConfigDict(from_attributes=True)

class Schedule(ScheduleBase):
    id: int
    assignee_id: List[int] = []
    assignee: List[Any] = []

    model_config = ConfigDict(from_attributes=True)
    
class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    where: Optional[str] = None
    assignee_id: Optional[List[int]] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
