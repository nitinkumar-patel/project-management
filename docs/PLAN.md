# Project Plan

This plan breaks the MVP into approval-sized parts. Complete one part at a time, check off its tasks as they are finished, run the listed tests, and pause for user approval at each approval gate before moving to the next part.

## Part 1: Plan

Goal: turn the project direction into an actionable implementation plan and document the existing frontend.

Checklist:
- [x] Expand `docs/PLAN.md` with detailed tasks, tests, and success criteria for each project part.
- [x] Create `frontend/AGENTS.md` describing the current frontend structure, commands, conventions, and test coverage.
- [x] Confirm the plan is concise and aligned with the project requirements in the root `AGENTS.md`.
- [x] Ask the user to review and approve the plan before Part 2 begins.

Tests:
- Documentation-only change; no automated tests required.
- Read the updated files for clarity and consistency.

Success criteria:
- The plan is specific enough that future work can proceed part by part.
- Frontend guidance reflects the actual Next.js demo app.
- User approval is requested before any scaffolding or implementation work.

Approval gate:
- User approves the plan.

## Part 2: Scaffolding

Goal: add the local Docker/FastAPI foundation and cross-platform start/stop scripts with a minimal working backend.

Checklist:
- [x] Create `backend/` with a minimal FastAPI app.
- [x] Add a health endpoint, such as `GET /api/health`, returning a small JSON payload.
- [x] Serve a simple static HTML page at `/` from FastAPI for the initial scaffold.
- [x] Add Python project files using `uv` for dependency management inside the Docker image.
- [x] Add Docker infrastructure for running the backend locally.
- [x] Add start and stop scripts for Mac, Linux, and Windows in `scripts/`.
- [x] Document the local run flow briefly in the root README or docs.
- [x] Keep `.env` secrets out of git and ensure generated runtime files are ignored.

Tests:
- [x] Backend unit test for the health endpoint.
- [x] Backend unit or integration test proving `/` serves HTML.
- [x] Manual script smoke test: start the app, call `/`, call `/api/health`, then stop the app.
- [x] Docker build succeeds from a clean checkout.

Success criteria:
- A local user can start and stop the container with the appropriate script.
- `GET /` returns example HTML.
- `GET /api/health` returns JSON.
- Backend tests pass.

Approval gate:
- User confirms the scaffold works locally and approves moving to frontend integration.

## Part 3: Add In Frontend

Goal: build the existing Next.js Kanban frontend as static assets and serve it from FastAPI at `/`.

Checklist:
- [ ] Configure the frontend for static export compatible with FastAPI static serving.
- [ ] Update the Docker build to install frontend dependencies and build the static site.
- [ ] Copy the static frontend build into the backend image.
- [ ] Replace the scaffold HTML at `/` with the built Kanban app.
- [ ] Preserve the current demo board behavior: render columns, rename columns, add cards, remove cards, and drag cards.
- [ ] Keep frontend code independent of backend persistence until Part 7.

Tests:
- [ ] Frontend unit tests pass with `npm run test:unit`.
- [ ] Frontend end-to-end tests pass with `npm run test:e2e`.
- [ ] Backend/static-serving test confirms `/` serves the frontend entry point.
- [ ] Docker smoke test confirms the Kanban board loads from the container.

Success criteria:
- The Kanban board is visible at `/` when the Docker app is running.
- Existing frontend behavior still works.
- Unit, end-to-end, and static-serving tests pass.

Approval gate:
- User confirms the static frontend is served correctly.

## Part 4: Add Fake User Sign In

Goal: require a local-only sign in before showing the Kanban board.

Checklist:
- [ ] Add a login screen at `/` when no session is active.
- [ ] Accept only username `user` and password `password`.
- [ ] Store the local session in the simplest appropriate browser-side state for the MVP.
- [ ] Show the Kanban board after successful login.
- [ ] Add a logout control that returns the user to the login screen.
- [ ] Show a clear error for invalid credentials.
- [ ] Avoid adding real authentication infrastructure in this MVP phase.

Tests:
- [ ] Unit tests for login form validation and successful login behavior.
- [ ] Unit tests for logout behavior.
- [ ] End-to-end test for invalid login.
- [ ] End-to-end test for successful login, board visibility, and logout.

Success criteria:
- Unauthenticated users cannot see the board.
- `user` / `password` signs in successfully.
- Logout clears the session.
- Tests cover the login/logout flow.

Approval gate:
- User approves the sign-in experience.

## Part 5: Database Modeling

Goal: propose and document the SQLite-backed Kanban data model before implementation.

Checklist:
- [ ] Define the future multi-user schema while supporting one board per signed-in user for the MVP.
- [ ] Model users, boards, columns, cards, card order, and timestamps.
- [ ] Decide how fixed-but-renamable columns are represented.
- [ ] Save the proposed schema as JSON in `docs/`.
- [ ] Document the database approach in `docs/`, including initialization and migration expectations.
- [ ] Identify API payload shapes needed by the frontend.
- [ ] Pause for user review before creating the database implementation.

Tests:
- Documentation-only phase; no automated tests required.
- Validate the schema JSON is well-formed.

Success criteria:
- The schema supports persistence for the current Kanban board.
- The schema can support multiple users later without redesigning the MVP.
- User signs off before backend database work starts.

Approval gate:
- User approves the database schema and approach.

## Part 6: Backend

Goal: add SQLite persistence and API routes for reading and changing a user's Kanban board.

Checklist:
- [ ] Add SQLite database initialization that creates the database if it does not exist.
- [ ] Add seed data for the hardcoded MVP user and one default board.
- [ ] Implement API routes to read the board for the current MVP user.
- [ ] Implement API routes to rename columns.
- [ ] Implement API routes to create, update, move, and delete cards.
- [ ] Keep request and response models explicit with Pydantic.
- [ ] Return useful HTTP errors for invalid board, column, or card operations.
- [ ] Keep the implementation simple and local-first.

Tests:
- [ ] Unit tests for database initialization and seed behavior.
- [ ] API tests for reading the default board.
- [ ] API tests for column rename.
- [ ] API tests for card create, update, move, and delete.
- [ ] API tests for invalid IDs and malformed requests.

Success criteria:
- Starting the backend creates a usable SQLite database when none exists.
- API routes persist Kanban changes.
- Backend tests thoroughly cover successful and invalid operations.

Approval gate:
- User approves the backend API behavior before wiring the frontend to it.

## Part 7: Frontend + Backend

Goal: make the frontend use the backend API so the Kanban board is persistent.

Checklist:
- [ ] Replace in-memory initial board state with an API load.
- [ ] Add simple loading and error states.
- [ ] Wire column rename to the backend.
- [ ] Wire card create, update, move, and delete to the backend.
- [ ] Refresh or update local state after successful API operations.
- [ ] Keep the UI responsive without adding complex state management.
- [ ] Ensure the Docker app serves the frontend and API from the same origin.

Tests:
- [ ] Unit tests for API client behavior, if an API client module is introduced.
- [ ] Component tests for loading, error, and successful board rendering states.
- [ ] End-to-end test showing a board change persists after reload.
- [ ] Backend tests from Part 6 still pass.
- [ ] Docker smoke test for the full app.

Success criteria:
- Board changes persist in SQLite.
- Reloading the page keeps renamed columns and changed cards.
- Frontend and backend tests pass.

Approval gate:
- User approves the persistent Kanban flow.

## Part 8: AI Connectivity

Goal: prove the backend can call OpenAI using the configured local environment.

Checklist:
- [ ] Add OpenAI client configuration using `OPENAI_API_KEY` from the environment.
- [ ] Use `gpt-4o-mini` as required.
- [ ] Add a minimal backend endpoint or test helper for an AI connectivity check.
- [ ] Send a simple "2+2" prompt and validate that a response is returned.
- [ ] Avoid exposing the API key to the frontend.
- [ ] Add clear error handling for missing or invalid API keys.

Tests:
- [ ] Unit tests with the OpenAI call mocked.
- [ ] Manual connectivity test using the real `OPENAI_API_KEY`.
- [ ] Test or documented check for missing API key behavior.

Success criteria:
- The backend can make a real OpenAI call locally.
- The API key remains server-side only.
- Mocked tests can run without external network access.

Approval gate:
- User confirms AI connectivity before adding board-aware AI behavior.

## Part 9: Board-Aware AI Backend

Goal: send the board, user question, and conversation history to the AI and receive structured output that can optionally update the board.

Checklist:
- [ ] Define the structured AI response schema for chat text and optional Kanban updates.
- [ ] Include the current board JSON, user question, and conversation history in the AI request.
- [ ] Support AI operations for creating, editing, and moving cards.
- [ ] Validate AI-proposed board updates before applying them.
- [ ] Persist valid AI updates to SQLite.
- [ ] Return both the assistant message and any applied board update summary.
- [ ] Keep conversation history scoped to the current local session unless persistence is explicitly added later.

Tests:
- [ ] Unit tests for structured response parsing.
- [ ] Unit tests for validating and applying AI board updates.
- [ ] API tests with mocked AI responses for no-op answers.
- [ ] API tests with mocked AI responses for create, edit, and move card operations.
- [ ] Regression tests ensuring invalid AI updates are rejected safely.

Success criteria:
- The AI endpoint returns a user-facing answer.
- Valid AI card updates are applied and persisted.
- Invalid structured outputs do not corrupt board data.
- Tests cover no-op and board-changing AI responses.

Approval gate:
- User approves the board-aware AI backend behavior.

## Part 10: AI Chat Sidebar

Goal: add a polished sidebar chat widget that lets the user ask the AI to discuss and update the Kanban board.

Checklist:
- [ ] Add a sidebar chat UI that fits the existing color scheme.
- [ ] Support sending user messages and displaying assistant responses.
- [ ] Show loading and error states for AI requests.
- [ ] Include conversation history in each backend AI call.
- [ ] Refresh or update the Kanban UI automatically when the AI changes the board.
- [ ] Make AI-applied changes clear to the user.
- [ ] Keep the layout usable on desktop and smaller screens.
- [ ] Preserve login and persistent board behavior.

Tests:
- [ ] Component tests for chat input, message rendering, loading, and error states.
- [ ] API-client tests for AI chat requests, if applicable.
- [ ] End-to-end test for asking a question that does not change the board.
- [ ] End-to-end test with mocked AI response that updates the board and refreshes the UI.
- [ ] Full regression test for login, board persistence, and AI chat.

Success criteria:
- The sidebar looks integrated with the app.
- Users can chat with the AI from the Kanban page.
- AI-initiated board updates appear without a manual page reload.
- Full test suite passes.

Approval gate:
- User approves the complete MVP.