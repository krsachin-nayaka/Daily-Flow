"""
app/routers/tasks.py

This module defines all HTTP route handlers (endpoints) for the /tasks resource.

Key FastAPI Concepts Illustrated:
1. APIRouter: Groups related endpoints under a common prefix ("/tasks") and tag ("Tasks").
2. Depends(get_db): Injects a fresh, isolated database session per request.
3. response_model: Instructs FastAPI to serialize the response using our Pydantic schema
   and document the shape in Swagger UI.
4. status_code: Specifies explicit HTTP status codes (e.g. 201 Created, 204 No Content).
5. HTTPException: Returns proper error status codes (e.g. 404 Not Found) with a JSON error payload.

IMPORTANT ROUTING LESSON:
Static routes like `/today` and `/stats` are placed BEFORE dynamic routes like `/{task_id}`.
If `/{task_id}` came first, FastAPI would capture "today" as `task_id` and fail with
a 422 error because "today" is not an integer!
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.task_schema import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStats,
    PriorityEnum,
    CategoryEnum,
)
from app.services import task_service

# Create an APIRouter instance
router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


# -----------------------------------------------------------------------------
# 1. Create a New Task
# -----------------------------------------------------------------------------
@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Validates incoming payload and creates a new task in SQLite."
)
def create_task_endpoint(
    task_in: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    Receives JSON body matching TaskCreate schema, calls task_service.create_task,
    and returns the created task serialized via TaskResponse.
    """
    return task_service.create_task(db=db, task_data=task_in)


# -----------------------------------------------------------------------------
# 2. Get All Tasks (with optional filtering)
# -----------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tasks",
    description="Retrieve all tasks, optionally filtered by category, priority, or completion status."
)
def get_all_tasks_endpoint(
    category: Optional[CategoryEnum] = Query(None, description="Filter by category"),
    priority: Optional[PriorityEnum] = Query(None, description="Filter by priority"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db)
):
    """
    Queries tasks with optional filters and returns a list of TaskResponse objects.
    """
    cat_val = category.value if category else None
    prio_val = priority.value if priority else None
    return task_service.get_all_tasks(
        db=db,
        category=cat_val,
        priority=prio_val,
        is_completed=is_completed
    )


# -----------------------------------------------------------------------------
# 3. Get Today's Tasks
# -----------------------------------------------------------------------------
@router.get(
    "/today",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get today's tasks",
    description="Retrieve all tasks whose due date equals today."
)
def get_today_tasks_endpoint(db: Session = Depends(get_db)):
    """
    Queries tasks where due_date == today's date.
    Placed BEFORE /{task_id} to prevent path conflict.
    """
    return task_service.get_today_tasks(db=db)


# -----------------------------------------------------------------------------
# 4. Get Task Statistics
# -----------------------------------------------------------------------------
@router.get(
    "/stats",
    response_model=TaskStats,
    status_code=status.HTTP_200_OK,
    summary="Get task statistics",
    description="Returns counts for total, completed, pending, and daily completion percentage."
)
def get_task_statistics_endpoint(db: Session = Depends(get_db)):
    """
    Calculates and returns counts and completion percentages.
    Placed BEFORE /{task_id} to prevent path conflict.
    """
    return task_service.get_task_statistics(db=db)


# -----------------------------------------------------------------------------
# 5. Get Specific Task by ID
# -----------------------------------------------------------------------------
@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific task",
    description="Retrieve a single task by its integer ID."
)
def get_task_by_id_endpoint(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetches a single task by primary key. Returns 404 if not found.
    """
    task = task_service.get_task_by_id(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return task


# -----------------------------------------------------------------------------
# 6. Update an Existing Task
# -----------------------------------------------------------------------------
@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task",
    description="Update fields of an existing task."
)
def update_task_endpoint(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates provided fields for the task. Returns 404 if the task doesn't exist.
    """
    updated_task = task_service.update_task(db=db, task_id=task_id, task_data=task_in)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return updated_task


# -----------------------------------------------------------------------------
# 7. Mark Task Completed / Toggle Status
# -----------------------------------------------------------------------------
@router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle task completion status",
    description="Toggles the completion status: pending becomes completed, completed becomes pending."
)
def toggle_task_complete_endpoint(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Toggles is_completed between True and False. Allows marking completed tasks
    as pending again as required.
    """
    toggled_task = task_service.toggle_task_completion(db=db, task_id=task_id)
    if not toggled_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return toggled_task


# -----------------------------------------------------------------------------
# 8. Delete a Task
# -----------------------------------------------------------------------------
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete task",
    description="Deletes a task by ID."
)
def delete_task_endpoint(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes the task. Returns a success message if deleted, 404 if not found.
    """
    success = task_service.delete_task(db=db, task_id=task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return {"message": f"Task {task_id} successfully deleted", "id": task_id}
