"""
app/database/models.py

Defines the SQLAlchemy ORM models for DailyFlow.
An ORM (Object-Relational Mapping) model is a regular Python class that maps
directly to a table in the relational SQLite database.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime
from app.database.connection import Base


class Task(Base):
    """
    SQLAlchemy model representing the 'tasks' table in SQLite.

    Each instance of this class corresponds to one row in the 'tasks' table.
    Attributes correspond to columns in that row.
    """
    __tablename__ = "tasks"

    # Primary key: uniquely identifies each task in the database
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Core task details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Task priority: High, Medium, Low
    priority = Column(String(20), nullable=False, default="Medium")

    # Category: DSA, Python, AI/ML, College, Gym, Personal
    category = Column(String(50), nullable=False, default="Personal")

    # Due date: stored as a date (YYYY-MM-DD)
    due_date = Column(Date, nullable=True)

    # Status flag: False = Pending, True = Completed
    is_completed = Column(Boolean, default=False, nullable=False)

    # Timestamps for audit and tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', priority='{self.priority}', completed={self.is_completed})>"
