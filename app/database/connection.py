"""
app/database/connection.py

This module manages the database connection and session lifecycle:
1. Defines the SQLite database URL.
2. Creates the SQLAlchemy Engine.
3. Configures the SessionLocal factory for creating database sessions.
4. Provides the Base class that all database models inherit from.
5. Provides the `get_db` dependency generator used by FastAPI endpoints.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# -----------------------------------------------------------------------------
# 1. Database Connection URL
# -----------------------------------------------------------------------------
# For SQLite, the URL format is: sqlite:///./<filename>.db
# The three slashes indicate a relative path from the current working directory.
DATABASE_URL = "sqlite:///./dailyflow.db"

# -----------------------------------------------------------------------------
# 2. SQLAlchemy Engine
# -----------------------------------------------------------------------------
# The Engine is the core interface to the database. It maintains connection pools
# and executes raw SQL under the hood.
#
# NOTE ON "check_same_thread": False:
# By default, SQLite only allows the thread that created the connection to communicate
# with it. In FastAPI, incoming HTTP requests can be handled by different threads.
# Setting "check_same_thread" to False allows multiple threads to safely use the
# connection across separate requests while each request still gets its own session.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True if you want to see raw SQL statements printed to the console
)

# -----------------------------------------------------------------------------
# 3. Session Factory (SessionLocal)
# -----------------------------------------------------------------------------
# SessionLocal is a factory function that creates a new database Session instance.
# - autocommit=False: We manually control transactions. Changes are only committed
#   when we explicitly call db.commit().
# - autoflush=False: Prevents SQLAlchemy from sending premature changes to the DB
#   before we are ready.
# - bind=engine: Binds this session factory to our SQLite engine.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -----------------------------------------------------------------------------
# 4. Declarative Base
# -----------------------------------------------------------------------------
# Base is the parent class for all SQLAlchemy ORM models.
# When we create classes like `class Task(Base):`, SQLAlchemy registers them
# in its metadata so it can create tables using `Base.metadata.create_all(bind=engine)`.
Base = declarative_base()

# -----------------------------------------------------------------------------
# 5. Database Session Dependency (FastAPI Depends)
# -----------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides an isolated database session per HTTP request.

    How it works:
    1. A new SQLAlchemy `db` session is instantiated for the incoming request.
    2. `yield db` gives the session to the router/service function.
    3. Once the request finishes (or if an unhandled exception occurs),
       execution resumes in the `finally` block.
    4. `db.close()` guarantees that the connection is cleanly returned
       and never leaked.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
