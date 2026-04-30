This directory contains the FastAPI backend for the Project Management MVP.

Current structure:
- `pyproject.toml` defines the Python project and test configuration.
- `src/project_management_backend/main.py` defines the FastAPI app.
- `src/project_management_backend/database.py` owns SQLite initialization, seed data, and Kanban persistence helpers.
- `src/project_management_backend/ai.py` owns OpenAI client setup and AI connectivity helpers.
- `src/project_management_backend/board_ai.py` validates and applies AI-proposed Kanban updates.
- `src/project_management_backend/schemas.py` defines Pydantic request and response models.
- `src/project_management_backend/static/` contains fallback static files for local backend-only runs.
- The Docker app sets `APP_STATIC_DIR` to the built frontend export directory.
- `tests/` contains backend tests.

Commands:
- Run backend commands from `backend/`.
- `uv run pytest` runs backend tests.
- `PYTHONPATH=src uv run uvicorn project_management_backend.main:app --host 0.0.0.0 --port 8000` runs the backend locally.

Conventions:
- Keep API routes under `/api/`.
- Keep the MVP board API scoped to the seeded `user` / `board-1` until real auth is added.
- Keep `OPENAI_API_KEY` server-side only; never expose it to frontend code.
- Validate AI-proposed board operations before applying them; invalid AI updates must not partially mutate the board.
- Serve frontend assets from `APP_STATIC_DIR` when the Docker image includes a built frontend.
- Keep server-only configuration and secrets out of frontend code.
- Store runtime SQLite data under `data/`, which should stay out of git.
- Keep the backend simple and local-first for the MVP.