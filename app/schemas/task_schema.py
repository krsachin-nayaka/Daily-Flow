"""
app/schemas/task_schema.py

This module defines Pydantic models (schemas).

Why Pydantic?
1. Request Validation: Automatically checks that incoming JSON matches expected types,
   lengths, and required fields. If invalid, returns HTTP 422 with clear error messages.
2. Response Serialization: Filters out unwanted database columns and serializes Python
   objects (like datetime/date) into JSON-compatible formats.
3. Interactive API Docs: FastAPI reads these schemas to auto-generate Swagger UI docs.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PriorityEnum(str, Enum):
    """Allowed priority values."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CategoryEnum(str, Enum):
    """Allowed categories as specified in the project requirements."""
    DSA = "DSA"
    PYTHON = "Python"
    AI_ML = "AI/ML"
    COLLEGE = "College"
    GYM = "Gym"
    PERSONAL = "Personal"


class TaskBase(BaseModel):
    """
    Shared attributes for tasks.
    Used as the parent class for create, update, and response schemas.
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Title of the task (required, max 200 characters)",
        examples=["Complete DSA Graph Problem Set"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional detailed description of the task",
        examples=["Solve 3 LeetCode medium questions on BFS/DFS"]
    )
    priority: PriorityEnum = Field(
        default=PriorityEnum.MEDIUM,
        description="Priority level: High, Medium, or Low"
    )
    category: CategoryEnum = Field(
        default=CategoryEnum.PERSONAL,
        description="Category: DSA, Python, AI/ML, College, Gym, or Personal"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Target completion date in YYYY-MM-DD format"
    )


class TaskCreate(TaskBase):
    """
    Schema for incoming task creation requests (POST /tasks/).
    Inherits all fields from TaskBase.
    `is_completed` is omitted here because a newly created task always starts as pending (False).
    """
    pass


class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task (PUT /tasks/{task_id}).
    All fields are Optional so the user can choose which attributes to modify.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    category: Optional[CategoryEnum] = None
    due_date: Optional[date] = None
    is_completed: Optional[bool] = None


class TaskResponse(TaskBase):
    """
    Schema for task data returned to the client (Response model).
    Includes database-generated fields: id, is_completed, created_at, updated_at.
    """
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    # Pydantic V2 configuration to allow reading data directly from SQLAlchemy ORM objects
    # (In Pydantic V1 this was `class Config: orm_mode = True`)
    model_config = ConfigDict(from_attributes=True)


class TaskStats(BaseModel):
    """
    Schema for task dashboard summary statistics.
    Returned by GET /tasks/stats.
    """
    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Total completed tasks")
    pending_tasks: int = Field(..., description="Total pending tasks")
    today_total: int = Field(..., description="Tasks scheduled for today")
    today_completed: int = Field(..., description="Tasks completed that were due today")
    completion_percentage: float = Field(..., description="Overall completion percentage (0 - 100)")
    today_completion_percentage: float = Field(..., description="Today's task completion percentage (0 - 100)")
