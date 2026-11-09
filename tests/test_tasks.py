"""
tests/test_tasks.py

Automated test suite for DailyFlow task endpoints using pytest and FastAPI TestClient.

Testing Concepts Demonstrated:
1. In-memory SQLite database (`sqlite:///:memory:`): Ensures each test run is isolated
   and does not pollute or touch the production database.
2. Dependency Overrides (`app.dependency_overrides`): FastAPI's powerful feature
   that allows swapping out the real database session for a test database session.
3. TestClient: Simulates HTTP requests against the FastAPI ASGI app without needing
   a running server process.
"""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import Base, get_db

# Create an in-memory SQLite database specifically for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency override function
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override to the FastAPI application
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """
    Runs before and after each test: creates clean tables before and drops them after.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """
    Provides a FastAPI TestClient instance for issuing HTTP requests.
    """
    return TestClient(app)


# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------

def test_create_task(client: TestClient):
    """Test creating a new task via POST /tasks/"""
    payload = {
        "title": "Study Binary Search Trees",
        "description": "Read chapter 4 and solve 2 problems",
        "priority": "High",
        "category": "DSA",
        "due_date": str(date.today())
    }
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["priority"] == "High"
    assert data["category"] == "DSA"
    assert data["is_completed"] is False
    assert "id" in data


def test_get_all_tasks(client: TestClient):
    """Test retrieving tasks with GET /tasks/"""
    client.post("/tasks/", json={"title": "Task 1", "category": "Python", "priority": "Low"})
    client.post("/tasks/", json={"title": "Task 2", "category": "DSA", "priority": "High"})

    response = client.get("/tasks/")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2


def test_get_today_tasks(client: TestClient):
    """Test retrieving only tasks due today with GET /tasks/today"""
    today_str = str(date.today())
    tomorrow_str = str(date.today() + timedelta(days=1))

    client.post("/tasks/", json={"title": "Today Task", "due_date": today_str})
    client.post("/tasks/", json={"title": "Tomorrow Task", "due_date": tomorrow_str})

    response = client.get("/tasks/today")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Today Task"


def test_get_task_by_id(client: TestClient):
    """Test retrieving a specific task by ID and handling 404 for missing tasks"""
    create_res = client.post("/tasks/", json={"title": "Specific Task"})
    task_id = create_res.json()["id"]

    # Valid task
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id

    # Non-existent task
    response_404 = client.get("/tasks/99999")
    assert response_404.status_code == 404


def test_update_task(client: TestClient):
    """Test updating task attributes via PUT /tasks/{id}"""
    create_res = client.post("/tasks/", json={"title": "Initial Title", "priority": "Low"})
    task_id = create_res.json()["id"]

    update_payload = {
        "title": "Updated Title",
        "priority": "High"
    }
    response = client.put(f"/tasks/{task_id}", json=update_payload)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["title"] == "Updated Title"
    assert updated_data["priority"] == "High"


def test_toggle_task_completion(client: TestClient):
    """Test marking task as completed and then toggling it back to pending"""
    create_res = client.post("/tasks/", json={"title": "Toggle Task"})
    task_id = create_res.json()["id"]

    # 1. First toggle: should become completed (True)
    res_completed = client.patch(f"/tasks/{task_id}/complete")
    assert res_completed.status_code == 200
    assert res_completed.json()["is_completed"] is True

    # 2. Second toggle: should become pending again (False)
    res_pending = client.patch(f"/tasks/{task_id}/complete")
    assert res_pending.status_code == 200
    assert res_pending.json()["is_completed"] is False


def test_delete_task(client: TestClient):
    """Test deleting a task via DELETE /tasks/{id}"""
    create_res = client.post("/tasks/", json={"title": "Task to Delete"})
    task_id = create_res.json()["id"]

    # Delete
    del_res = client.delete(f"/tasks/{task_id}")
    assert del_res.status_code == 200

    # Ensure it no longer exists
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404


def test_task_statistics(client: TestClient):
    """Test statistics endpoint GET /tasks/stats"""
    today_str = str(date.today())

    # Task 1: today, completed
    res1 = client.post("/tasks/", json={"title": "T1", "due_date": today_str})
    t1_id = res1.json()["id"]
    client.patch(f"/tasks/{t1_id}/complete")

    # Task 2: today, pending
    client.post("/tasks/", json={"title": "T2", "due_date": today_str})

    # Task 3: future, pending
    future_str = str(date.today() + timedelta(days=5))
    client.post("/tasks/", json={"title": "T3", "due_date": future_str})

    stats_res = client.get("/tasks/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()

    assert stats["total_tasks"] == 3
    assert stats["completed_tasks"] == 1
    assert stats["pending_tasks"] == 2
    assert stats["today_total"] == 2
    assert stats["today_completed"] == 1
    assert stats["today_completion_percentage"] == 50.0
    assert stats["completion_percentage"] == round(1 / 3 * 100, 1)
