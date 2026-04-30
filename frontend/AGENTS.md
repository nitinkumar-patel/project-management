# Frontend Guidance

This directory contains the Kanban frontend. It is a Next.js App Router app using React, TypeScript, Tailwind CSS, and `@dnd-kit` for drag and drop.

## Current Structure

- `src/app/page.tsx` renders the Kanban board at `/`.
- `src/app/layout.tsx` defines app metadata, Google fonts, and the root layout.
- `src/app/globals.css` defines Tailwind setup, project color variables, and global typography.
- `src/components/ProjectApp.tsx` owns the local MVP sign-in gate and session state.
- `src/components/LoginForm.tsx` renders the hardcoded local sign-in form.
- `src/components/KanbanBoard.tsx` loads board state from the backend API and sends board mutations back to the API.
- `src/components/KanbanColumn.tsx` renders a droppable column, editable column title, cards, and the add-card form.
- `src/components/KanbanCard.tsx` renders an individual draggable card and remove action.
- `src/components/KanbanCardPreview.tsx` renders the drag overlay preview.
- `src/components/NewCardForm.tsx` handles the inline add-card form.
- `src/lib/api.ts` contains frontend API helpers for board operations.
- `src/lib/kanban.ts` contains board types and legacy demo helpers.
- `src/test/` contains Vitest setup files.
- `tests/` contains Playwright end-to-end tests.

## Current Behavior

- The board is loaded from the backend API and persisted in SQLite.
- There are five fixed columns from the backend seed data, but their titles can be renamed in the UI.
- Cards can be added, removed, reordered, and moved between columns.
- The app requires the hardcoded MVP credentials `user` and `password` before showing the board.
- AI chat is not currently wired into the frontend.

## Commands

Run commands from this `frontend/` directory.

- `npm run dev` starts the Next.js dev server.
- `npm run build` builds the frontend.
- `npm run lint` runs ESLint.
- `npm run test:unit` runs Vitest unit/component tests.
- `npm run test:e2e` runs Playwright end-to-end tests against a real local backend test database.
- `npm run test:all` runs unit tests and end-to-end tests.

## Testing Expectations

- Add or update Vitest tests for pure logic and component behavior in `src/`.
- Add or update Playwright tests for user-visible flows in `tests/`.
- Keep existing board tests passing when changing Kanban behavior.
- Mock API calls in focused unit/component tests and use Playwright for the real frontend/backend flow.

## Conventions

- Keep components small and specific; use the current component split unless a feature clearly needs a new component.
- Keep board data shapes aligned with the backend API response.
- Preserve the project color variables from `src/app/globals.css`.
- Do not expose server-only secrets, including `OPENAI_API_KEY`, to frontend code.
- Keep the hardcoded sign-in local-only until real authentication is added.
- Keep implementation simple for the MVP; avoid adding global state libraries unless the app outgrows local state and straightforward API calls.
