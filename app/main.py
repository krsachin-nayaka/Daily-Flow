"""
app/main.py

The main entry point of the DailyFlow application.

Responsibilities:
1. Initialize the FastAPI application instance with metadata.
2. Ensure database tables are created on startup (Base.metadata.create_all).
3. Mount static assets (CSS, JavaScript, images) at /static.
4. Configure Jinja2 templates directory for server-rendered HTML.
5. Register API routers (tasks router).
6. Serve the main dashboard at GET /.
7. Start the Uvicorn ASGI server when executed directly.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from app.database.connection import engine, Base
from app.routers.tasks import router as tasks_router


# -----------------------------------------------------------------------------
# 1. Lifespan Event Handler (Startup & Shutdown)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager runs code before the app starts accepting requests,
    and after the app finishes shutting down.

    Here we ensure all SQLAlchemy tables (e.g. 'tasks') are automatically created
    in SQLite if they don't already exist.
    """
    # Create SQLite database tables based on our ORM models
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if any) can go here


# -----------------------------------------------------------------------------
# 2. FastAPI Application Instance
# -----------------------------------------------------------------------------
app = FastAPI(
    title="DailyFlow – Personal Task Manager",
    description="A lightweight, clean, and educational task manager built with FastAPI, SQLAlchemy, and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",      # Interactive Swagger UI documentation
    redoc_url="/redoc"    # Alternative ReDoc documentation
)

# -----------------------------------------------------------------------------
# 3. CORS Middleware Configuration
# -----------------------------------------------------------------------------
# Allows the frontend (or external API clients) to make HTTP requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# 4. Static Files and Templates Setup
# -----------------------------------------------------------------------------
# Determine base paths so paths work regardless of current working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Mount /static URL to the app/static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 HTML templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# -----------------------------------------------------------------------------
# 5. Root Dashboard Route
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard(request: Request):
    """
    Renders and serves the DailyFlow dashboard HTML page.
    The page then communicates with our /tasks endpoints using the JavaScript Fetch API.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# -----------------------------------------------------------------------------
# 6. Include API Routers
# -----------------------------------------------------------------------------
# Mount all task endpoints under /tasks
app.include_router(tasks_router)


# -----------------------------------------------------------------------------
# 7. Uvicorn Server Starter
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Allows running this file directly: python app/main.py
    # Runs on port 3000 to match the environment's web port
    uvicorn.run("app.main:app", host="0.0.0.0", port=3000, reload=True)
