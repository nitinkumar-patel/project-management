This directory contains the FastAPI backend for the Project Management MVP.

Current structure:
- `pyproject.toml` defines the Python project and test configuration.
- `src/project_management_backend/main.py` defines the FastAPI app.
- `src/project_management_backend/static/` contains fallback static files for local backend-only runs.
- The Docker app sets `APP_STATIC_DIR` to the built frontend export directory.
- `tests/` contains backend tests.

Commands:
- Run backend commands from `backend/`.
- `uv run pytest` runs backend tests.
- `uv run uvicorn project_management_backend.main:app --host 0.0.0.0 --port 8000` runs the backend locally.

Conventions:
- Keep API routes under `/api/`.
- Serve frontend assets from `APP_STATIC_DIR` when the Docker image includes a built frontend.
- Keep server-only configuration and secrets out of frontend code.
- Use SQLite for persistence when the database phase begins.
- Keep the backend simple and local-first for the MVP.