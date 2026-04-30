This directory contains the FastAPI backend for the Project Management MVP.

Current structure:
- `pyproject.toml` defines the Python project and test configuration.
- `src/project_management_backend/main.py` defines the FastAPI app.
- `src/project_management_backend/static/` contains scaffold static files served by the backend.
- `tests/` contains backend tests.

Commands:
- Run backend commands from `backend/`.
- `uv run pytest` runs backend tests.
- `uv run uvicorn project_management_backend.main:app --host 0.0.0.0 --port 8000` runs the backend locally.

Conventions:
- Keep API routes under `/api/`.
- Keep server-only configuration and secrets out of frontend code.
- Use SQLite for persistence when the database phase begins.
- Keep the backend simple and local-first for the MVP.