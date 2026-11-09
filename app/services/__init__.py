"""
Service layer containing business logic and database CRUD operations.
"""
from app.services.task_service import (
    get_all_tasks,
    get_today_tasks,
    get_task_by_id,
    create_task,
    update_task,
    toggle_task_completion,
    delete_task,
    get_task_statistics,
)

__all__ = [
    "get_all_tasks",
    "get_today_tasks",
    "get_task_by_id",
    "create_task",
    "update_task",
    "toggle_task_completion",
    "delete_task",
    "get_task_statistics",
]
