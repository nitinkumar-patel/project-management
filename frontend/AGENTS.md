# Frontend Guidance

This directory contains the current frontend-only Kanban demo. It is a Next.js App Router app using React, TypeScript, Tailwind CSS, and `@dnd-kit` for drag and drop.

## Current Structure

- `src/app/page.tsx` renders the Kanban board at `/`.
- `src/app/layout.tsx` defines app metadata, Google fonts, and the root layout.
- `src/app/globals.css` defines Tailwind setup, project color variables, and global typography.
- `src/components/KanbanBoard.tsx` owns the current in-memory board state and drag/drop handlers.
- `src/components/KanbanColumn.tsx` renders a droppable column, editable column title, cards, and the add-card form.
- `src/components/KanbanCard.tsx` renders an individual draggable card and remove action.
- `src/components/KanbanCardPreview.tsx` renders the drag overlay preview.
- `src/components/NewCardForm.tsx` handles the inline add-card form.
- `src/lib/kanban.ts` contains board types, demo seed data, ID generation, and card movement logic.
- `src/test/` contains Vitest setup files.
- `tests/` contains Playwright end-to-end tests.

## Current Behavior

- The board is entirely client-side and resets on page refresh.
- There are five fixed columns in the seed data, but their titles can be renamed in the UI.
- Cards can be added, removed, reordered, and moved between columns.
- No login, backend API, persistence, or AI chat is currently wired into the frontend.

## Commands

Run commands from this `frontend/` directory.

- `npm run dev` starts the Next.js dev server.
- `npm run build` builds the frontend.
- `npm run lint` runs ESLint.
- `npm run test:unit` runs Vitest unit/component tests.
- `npm run test:e2e` runs Playwright end-to-end tests.
- `npm run test:all` runs unit tests and end-to-end tests.

## Testing Expectations

- Add or update Vitest tests for pure logic and component behavior in `src/`.
- Add or update Playwright tests for user-visible flows in `tests/`.
- Keep existing board tests passing when changing Kanban behavior.
- When frontend work depends on backend behavior, prefer mocking only where needed for focused component tests and use end-to-end coverage for the full flow.

## Conventions

- Keep components small and specific; use the current component split unless a feature clearly needs a new component.
- Keep board data shapes aligned with `src/lib/kanban.ts` until the backend schema replaces them.
- Preserve the project color variables from `src/app/globals.css`.
- Do not expose server-only secrets, including `OPENAI_API_KEY`, to frontend code.
- Keep implementation simple for the MVP; avoid adding global state libraries unless the app outgrows local state and straightforward API calls.
