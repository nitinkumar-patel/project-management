# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A single-user Kanban project management app with an AI-powered chat assistant. Users can manage tasks across a 5-column board (drag-and-drop), rename columns, and ask the AI to create, edit, or move cards on their behalf.

**Stack:** Next.js 16 frontend (statically built, served by FastAPI) + Python FastAPI backend + SQLite + OpenAI `gpt-4o-mini`

**Deployment:** Single Docker container — frontend is built as a static export and bundled into the backend image, which serves it from `/`.

**Scope:** MVP with one hardcoded user (`user` / `password`), one board per user, and conversation history held in-memory (not persisted).

## Commands

### Frontend (`frontend/`)
```bash
npm run dev              # Dev server on port 3210
npm run build            # Static export to ./out/ (served by FastAPI)
npm run lint             # ESLint
npm run test:unit        # Vitest unit/integration tests
npm run test:unit:watch  # Watch mode
npm run test:e2e         # Playwright browser tests
npm run test:all         # Run all tests
```

### Backend (`backend/`)
```bash
uv run uvicorn project_management_backend.main:app --reload --port 8010
uv run pytest            # All backend tests
uv run pytest tests/test_app.py::test_name  # Single test
```

### Docker (full stack)
```bash
docker compose up --build   # Build and start on port 8000
docker compose down
```

## Architecture

**Single-user Kanban MVP.** Hardcoded credentials: `user` / `password`. Authentication is stored in `sessionStorage` with key `project-management-authenticated`.

### Frontend (Next.js 16, App Router, React 19, Tailwind 4)
- `src/app/page.tsx` → renders `ProjectApp`
- `ProjectApp` gates auth; renders `LoginForm` or `KanbanBoard`
- `KanbanBoard` owns board state; columns are fixed (5), card order is persisted
- Drag-and-drop via `@dnd-kit` (PointerSensor, 6px threshold, closestCorners collision)
- `AiChatSidebar` maintains conversation history in component state; sends full history + board context on each message
- All API calls go through `lib/api.ts` (typed fetch wrapper)
- `next.config.ts` uses `output: "export"` — the built `./out/` is served statically by the FastAPI backend
- Path alias: `@/*` → `src/*`

### Backend (FastAPI, SQLite, OpenAI `gpt-4o-mini`)
- `main.py` — all routes, CORS, lifespan DB init
- `database.py` — raw SQLite (no ORM); foreign keys enabled; cascade deletes
- `board_ai.py` — structured AI output: `AiStructuredOutput` with a message and operations list (`create_card`, `edit_card`, `move_card`); invalid operations are rejected entirely (no partial mutations)
- One board per user (unique index on `user_id`); 5 fixed columns with mutable titles
- Error classes: `NotFoundError` → 404, `MissingApiKeyError` → 503, `InvalidAiOperationError` → 502

### API Routes
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health check |
| GET | `/api/board` | Fetch user's board (columns + cards) |
| PATCH | `/api/columns/{id}` | Rename column |
| POST | `/api/cards` | Create card |
| PATCH | `/api/cards/{id}` | Edit card |
| POST | `/api/cards/{id}/move` | Move card to column/position |
| DELETE | `/api/cards/{id}` | Delete card |
| POST | `/api/ai/chat` | Board-aware AI chat |
| POST | `/api/ai/connectivity` | Test OpenAI key |

### Testing
- **Unit/integration (Vitest):** `src/**/*.test.{ts,tsx}` — jsdom env, `@testing-library/react`
- **E2E (Playwright):** `tests/kanban.spec.ts` — spins up backend on port 8010 with `playwright.sqlite3`, frontend on port 3210 with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010`
- **Backend (pytest):** `backend/tests/test_app.py` — `TestClient` + temp SQLite per test, monkeypatch for OpenAI

### Design System
CSS variables in `globals.css`:
- `--accent-yellow: #ecad0a`
- `--primary-blue: #209dd7`
- `--secondary-purple: #753991`
- `--navy-dark: #032147`
- `--gray-text: #888888`

Fonts: **Manrope** (`--font-body`), **Space_Grotesk** (`--font-display`) loaded via Next.js Google Fonts.

Components use Tailwind's `bg-[var(...)]` / `text-[var(...)]` pattern.

### Environment
- `OPENAI_API_KEY` — required for AI features; set in `.env` at repo root (git-ignored)
- `NEXT_PUBLIC_API_BASE_URL` — overrides API base in frontend (used by Playwright)
