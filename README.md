# DailyFlow – Personal Task Manager

DailyFlow is a clean, modern personal task management web application built from the ground up for learning backend engineering with **Python**, **FastAPI**, **SQLAlchemy ORM**, **SQLite**, **Pydantic**, and a responsive **HTML5/CSS3/Vanilla JavaScript** frontend.

---

## 1. Architecture & Request-Response Flow

DailyFlow follows a clean layered architecture with strict separation of concerns:

```
+-------------------------------------------------------------------+
|                           FRONTEND                                |
|  HTML5 (app/templates/index.html) + CSS3 + Vanilla JS (app.js)    |
|                Communicates via window.fetch()                    |
+---------------------------------+---------------------------------+
                                  | HTTP Requests (JSON)
                                  v
+---------------------------------+---------------------------------+
|                        FASTAPI ROUTER                             |
|                    (app/routers/tasks.py)                         |
|  - Validates request payloads with Pydantic Schemas               |
|  - Dispatches to business logic                                   |
|  - Formats responses & HTTP status codes                          |
+---------------------------------+---------------------------------+
                                  | Function Calls
                                  v
+---------------------------------+---------------------------------+
|                        SERVICE LAYER                              |
|                   (app/services/task_service.py)                  |
|  - Encapsulates business rules and CRUD queries                   |
|  - Calculates statistics and percentages                          |
+---------------------------------+---------------------------------+
                                  | Session operations
                                  v
+---------------------------------+---------------------------------+
|                       SQLALCHEMY ORM                              |
|   (app/database/connection.py & app/database/models.py)           |
|  - Translates Python Task objects into SQL queries                |
|  - Manages SQLite connection pooling and transactions             |
+---------------------------------+---------------------------------+
                                  | SQL Queries
                                  v
+---------------------------------+---------------------------------+
|                       SQLITE DATABASE                             |
|                        (dailyflow.db)                             |
+-------------------------------------------------------------------+
```

### Complete Request Lifecycle Example (Creating a Task):

1. **User Action:** The user fills out the task title, category, priority, and due date in the browser, then clicks **Save Task**.
2. **Frontend `app.js`:** Captures the form event, constructs a JSON payload, and calls `fetch("/tasks/", { method: "POST", body: JSON.stringify(...) })`.
3. **FastAPI `tasks.py`:** Intercepts `POST /tasks/`. It injects the database session via `db: Session = Depends(get_db)` and validates the body against the `TaskCreate` Pydantic schema.
4. **Service `task_service.py`:** Receives `task_data: TaskCreate` and `db: Session`. It creates an instance of the `Task` ORM model, stages it with `db.add()`, commits it to SQLite with `db.commit()`, and refreshes the model with `db.refresh()`.
5. **Response:** FastAPI serializes the `Task` instance into a `TaskResponse` schema (converting datetime/date objects to ISO format) and returns an HTTP `201 Created` status with the new task JSON.
6. **Frontend Update:** `app.js` receives the response, shows a toast notification ("Task created successfully!"), closes the modal, and refetches the list and statistics.

---

## 2. Project Folder Structure

```
DailyFlow/
├── app/
│   ├── __init__.py               # Marks app as a Python package
│   ├── main.py                   # FastAPI initialization, static mounting, router inclusion
│   │
│   ├── database/
│   │   ├── __init__.py           # Re-exports Base, engine, get_db, Task
│   │   ├── connection.py         # SQLite engine, sessionmaker, and get_db dependency
│   │   └── models.py             # SQLAlchemy Task ORM model
│   │
│   ├── schemas/
│   │   ├── __init__.py           # Re-exports Pydantic schemas and enums
│   │   └── task_schema.py        # TaskCreate, TaskUpdate, TaskResponse, TaskStats
│   │
│   ├── routers/
│   │   ├── __init__.py           # Re-exports tasks router
│   │   └── tasks.py              # HTTP endpoints for /tasks
│   │
│   ├── services/
│   │   ├── __init__.py           # Re-exports service functions
│   │   └── task_service.py       # CRUD operations and dashboard statistics calculation
│   │
│   ├── templates/
│   │   └── index.html            # Dashboard HTML layout
│   │
│   └── static/
│       ├── css/
│       │   └── style.css         # Dark Navy + Teal/Cyan styling
│       ├── js/
│       │   └── app.js            # Vanilla JS state, Fetch API, and DOM rendering
│       └── images/               # Static images/icons
│
├── tests/
│   ├── __init__.py
│   └── test_tasks.py             # Automated pytest suite with in-memory SQLite
│
├── .gitignore                    # Python, SQLite, environment files git ignore
├── pyproject.toml                # Project metadata and dependencies managed by uv
└── README.md                     # Comprehensive technical guide
```

---

## 3. Installation & Setup with `uv`

[`uv`](https://github.com/astral-sh/uv) is an extremely fast Python package manager and resolver written in Rust.

### Step 1: Install `uv` (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Create a virtual environment
```bash
uv venv
```
Activate the virtual environment:
- On Linux/macOS:
  ```bash
  source .venv/bin/activate
  ```
- On Windows:
  ```powershell
  .venv\Scripts\activate
  ```

### Step 3: Install dependencies
Install project dependencies along with development testing tools:
```bash
uv pip install -e ".[dev]"
```

---

## 4. Running the Application

### Option A: Using `uv run` (Recommended)
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Option B: Running directly with Python
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

---

## 5. Accessing the Dashboard & Swagger UI

Once the server is running:

- **Web Dashboard:** Open [http://localhost:3000](http://localhost:3000) in your web browser.
- **Interactive Swagger UI:** Open [http://localhost:3000/docs](http://localhost:3000/docs) to explore and interactively test every API endpoint.
- **ReDoc Documentation:** Open [http://localhost:3000/redoc](http://localhost:3000/redoc) for clean reference documentation.

---

## 6. Running Automated Tests

DailyFlow includes a comprehensive automated test suite in `tests/test_tasks.py` that validates all CRUD endpoints, filters, edge cases, and statistics calculations using an in-memory SQLite database:

```bash
uv run pytest -v
```

---

## 7. API Reference Table

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/tasks/` | Create a new task | `201 Created` |
| `GET` | `/tasks/` | Get all tasks (supports query filters for `category`, `priority`, `is_completed`) | `200 OK` |
| `GET` | `/tasks/today` | Get tasks scheduled for today | `200 OK` |
| `GET` | `/tasks/stats` | Get dashboard statistics (total, completed, pending, completion %) | `200 OK` |
| `GET` | `/tasks/{task_id}` | Get a specific task by primary key ID | `200 OK` / `404` |
| `PUT` | `/tasks/{task_id}` | Update fields of an existing task | `200 OK` / `404` |
| `PATCH`| `/tasks/{task_id}/complete` | Toggle task completion (pending <-> completed) | `200 OK` / `404` |
| `DELETE`| `/tasks/{task_id}` | Delete a task by ID | `200 OK` / `404` |

---

## 8. Detailed File-by-File Technical Guide

### `app/database/connection.py`
- **What it does:** Sets up the SQLite database connection, engine, session maker, base model, and the `get_db` generator.
- **Why we need it:** Relational databases require connection pools and transaction management. In web applications, each HTTP request must have its own isolated transaction so that simultaneous requests don't interfere with each other.
- **Key Concepts:**
  - `create_engine("sqlite:///./dailyflow.db", connect_args={"check_same_thread": False})`: SQLite restricts connections to one thread by default; FastAPI processes requests across worker threads, so `check_same_thread: False` is necessary.
  - `sessionmaker`: A factory for creating database sessions.
  - `get_db()`: Uses Python's `yield` statement. When FastAPI calls `Depends(get_db)`, it generates a session, yields it to the router, and guarantees `db.close()` runs in the `finally` block when the response is sent.

### `app/database/models.py`
- **What it does:** Defines the `Task` class inheriting from `Base`.
- **Why we need it:** Instead of writing raw SQL strings (`CREATE TABLE tasks...`), SQLAlchemy ORM maps Python class attributes directly to database table columns.
- **Fields:**
  - `id`: Auto-incrementing primary key.
  - `title`: String up to 200 characters, required.
  - `description`: Optional text.
  - `priority`: High, Medium, or Low.
  - `category`: DSA, Python, AI/ML, College, Gym, or Personal.
  - `due_date`: Date (YYYY-MM-DD).
  - `is_completed`: Boolean flag (default `False`).
  - `created_at` & `updated_at`: UTC timestamps.

### `app/schemas/task_schema.py`
- **What it does:** Defines Pydantic validation schemas.
- **Why we need it:** Separates what the database stores (`models.py`) from what the API accepts and returns (`schemas/task_schema.py`).
  - `TaskCreate`: Ensures incoming data has a valid title, valid priority enum, and valid category before any SQL executes.
  - `TaskUpdate`: Makes all fields optional so clients can update only what changed.
  - `TaskResponse`: Uses `ConfigDict(from_attributes=True)` so Pydantic can read attributes directly from SQLAlchemy objects and serialize them to JSON.
  - `TaskStats`: Defines the schema for dashboard metrics.

### `app/services/task_service.py`
- **What it does:** Pure business and database logic.
- **Why we need it:** Prevents API route handlers from becoming bloated. If we ever want to build a CLI or background job, we can call `task_service.create_task()` directly without simulating an HTTP request.
- **Operations:** `get_all_tasks`, `get_today_tasks`, `get_task_by_id`, `create_task`, `update_task`, `toggle_task_completion`, `delete_task`, `get_task_statistics`.

### `app/routers/tasks.py`
- **What it does:** Connects incoming HTTP requests to service functions.
- **Why we need it:** Handles HTTP-specific duties: reading query parameters, parsing URL path parameters, applying HTTP status codes (`201`, `404`), and returning structured JSON.
- **Routing Lesson:** Notice that static routes (`/today` and `/stats`) are declared before parameterized routes (`/{task_id}`). If `/{task_id}` were placed first, FastAPI would mistake `"today"` for an integer task ID and return an HTTP 422 error!

### `app/main.py`
- **What it does:** The central FastAPI app.
- **Why we need it:** Glues all pieces together. Configures CORS, mounts `/static` for CSS and JavaScript, configures Jinja2 templates, registers the task router, and ensures SQLite tables are created on startup via `@asynccontextmanager lifespan`.
