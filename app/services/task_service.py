"""
app/services/task_service.py

This module implements the business logic (Service Layer) for DailyFlow.

Why a Service Layer?
- Keeps Routers clean: Routers only handle HTTP (request parsing, status codes, headers).
- Keeps Database logic reusable: Any router, CLI command, or background job can call
  these service functions without repeating SQLAlchemy queries.
- Easier to test: Service functions can be unit-tested directly with a database session.
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import Task
from app.schemas.task_schema import TaskCreate, TaskUpdate


def get_all_tasks(
    db: Session,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    is_completed: Optional[bool] = None
) -> List[Task]:
    """
    Retrieve all tasks from the database, with optional filtering.

    - db: Active SQLAlchemy session.
    - category: Filter by category (e.g. 'DSA', 'Python').
    - priority: Filter by priority ('High', 'Medium', 'Low').
    - is_completed: Filter by completion state (True or False).
    """
    query = db.query(Task)

    if category:
        query = query.filter(Task.category == category)
    if priority:
        query = query.filter(Task.priority == priority)
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)

    # Order by due_date ascending (nulls last), then id descending
    return query.order_by(Task.due_date.asc().nullslast(), Task.id.desc()).all()


def get_today_tasks(db: Session) -> List[Task]:
    """
    Retrieve all tasks whose due_date matches today's date.
    """
    today = date.today()
    return (
        db.query(Task)
        .filter(Task.due_date == today)
        .order_by(Task.is_completed.asc(), Task.priority.desc(), Task.id.desc())
        .all()
    )


def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    """
    Find a specific task by its unique primary key ID.
    Returns None if no task matches the given ID.
    """
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, task_data: TaskCreate) -> Task:
    """
    Create and persist a new task in the database.

    How it works:
    1. Converts Pydantic model into a Python dictionary via .model_dump().
    2. Instantiates a new SQLAlchemy Task ORM object.
    3. db.add(): Stages the new object in the current transaction.
    4. db.commit(): Flushes and commits the SQL INSERT statement to SQLite.
    5. db.refresh(): Reloads the object from the DB so generated fields
       (like auto-increment ID and timestamps) are available on the Python object.
    """
    # model_dump() is the Pydantic v2 equivalent of v1's .dict()
    task_dict = task_data.model_dump()
    new_task = Task(**task_dict)

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
    """
    Update an existing task by ID with only the fields provided.

    Uses exclude_unset=True so only fields explicitly supplied in the request
    body are updated, leaving untouched fields as they were.
    """
    task = get_task_by_id(db, task_id)
    if not task:
        return None

    # Only extract fields that were explicitly set in the request
    update_data = task_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task


def toggle_task_completion(db: Session, task_id: int) -> Optional[Task]:
    """
    Toggle the completion status of a task:
    - If False (pending) -> becomes True (completed).
    - If True (completed) -> becomes False (pending again).

    This satisfies both:
    1. "Mark tasks as completed"
    2. "Mark completed tasks as pending again"
    """
    task = get_task_by_id(db, task_id)
    if not task:
        return None

    task.is_completed = not task.is_completed
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    """
    Delete a task from the database.
    Returns True if the task was found and deleted, False otherwise.
    """
    task = get_task_by_id(db, task_id)
    if not task:
        return False

    db.delete(task)
    db.commit()
    return True


def get_task_statistics(db: Session) -> dict:
    """
    Calculate summary statistics for the dashboard:
    - Total tasks count
    - Completed tasks count
    - Pending tasks count
    - Today's total tasks
    - Today's completed tasks
    - Overall completion percentage
    - Today's completion percentage
    """
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.is_completed == True).count()
    pending_tasks = total_tasks - completed_tasks

    today = date.today()
    today_total = db.query(Task).filter(Task.due_date == today).count()
    today_completed = (
        db.query(Task)
        .filter(Task.due_date == today, Task.is_completed == True)
        .count()
    )

    # Calculate percentages safely (avoid zero division)
    if total_tasks > 0:
        completion_percentage = round((completed_tasks / total_tasks) * 100, 1)
    else:
        completion_percentage = 0.0

    if today_total > 0:
        today_completion_percentage = round((today_completed / today_total) * 100, 1)
    else:
        today_completion_percentage = 0.0

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "today_total": today_total,
        "today_completed": today_completed,
        "completion_percentage": completion_percentage,
        "today_completion_percentage": today_completion_percentage,
    }
