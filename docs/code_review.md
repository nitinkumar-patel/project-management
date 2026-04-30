# Code Review

Date: 2026-04-30

## Summary

This is a clean, well-structured single-user Kanban MVP. The backend uses parameterized queries throughout (no SQL injection risk), the frontend enforces TypeScript strict mode, and all 54 tests pass. The two most urgent issues are a real OpenAI API key committed in plain text inside the `.env` file (the key exists on disk — it must be rotated immediately) and a client-side-only authentication model where credentials are hardcoded in JavaScript source code that ships to every browser. Beyond those, the main risk areas are non-atomic AI multi-operation execution, a missing `delete_card` test against the backend operation type, and a drag-drop position calculation that can place a card one slot off when reordering within the same column.

---

## Findings

### Critical

#### LIVE API KEY IN REPOSITORY ROOT `.env`
- **File:** `.env:2`
- **Problem:** The file contains a full `sk-proj-...` OpenAI key. Although `.env` is in `.gitignore` and does not appear in git history, the file is sitting on disk and is copied into Docker build context. `docker build` does not copy it (`.dockerignore` excludes `.env`), but anyone with filesystem access to this machine — or any future `git add -A` accident — exposes the key. More critically, the key should be treated as compromised the moment it exists in a plain-text file at a shared repo root.
- **Fix:** Rotate this key in the OpenAI dashboard right now. Store it only in the environment (shell profile, secret manager, or Docker `--env-file` at run time). Never check it in or leave it at the repo root.

#### HARDCODED CREDENTIALS IN SHIPPED JAVASCRIPT
- **File:** `frontend/src/components/LoginForm.tsx:9-10`
- **Problem:** `VALID_USERNAME = "user"` and `VALID_PASSWORD = "password"` are compiled directly into the static export bundle. Any user who opens DevTools or inspects the network bundle can read them. This is an MVP and a single user, but the credentials gate the board, so the protection is entirely illusory — the "login" provides no real access control because the check runs client-side and the API accepts requests from anyone with no token.
- **Fix:** For the MVP, acknowledge the limitation in comments and perhaps add a one-line UI note saying "demo credentials". For any real deployment, move authentication server-side: issue a session cookie or JWT on the backend and require it on every API route. The database schema already has a `users` table — the infrastructure is ready.

---

### High

#### AI OPERATIONS ARE NOT ATOMIC — PARTIAL MUTATION IS POSSIBLE
- **File:** `backend/src/project_management_backend/board_ai.py:29-74`
- **Problem:** `validate_operations()` validates all operations against the board snapshot taken *before* any mutations. Then `apply_operations()` executes them one by one. If the second operation fails (e.g., a database error on `database.update_card()`), the first operation's change is already committed. The board is left in a partially-updated state, and the HTTP response is a 500 with no indication of what succeeded.
- **Fix:** Wrap the entire loop in a single `sqlite3` transaction. Pass the connection object through `apply_operations` or restructure `database.py` to support explicit transaction boundaries. Alternatively, collect all DB calls and execute them atomically using `connection.executemany` inside one `with connect()` block.

#### CORS ALLOWS ANY METHOD AND HEADER FROM DEV ORIGINS IN PRODUCTION IMAGE
- **File:** `backend/src/project_management_backend/main.py:35-40`
- **Problem:** `allow_origins=["http://127.0.0.1:3210", "http://localhost:3210"]` with `allow_methods=["*"]` and `allow_headers=["*"]`. In the Docker image the frontend is served by the same FastAPI process on port 8000, so browser requests are same-origin and CORS is irrelevant. However these two dev origins remain unrestricted in production. More importantly, `allow_methods=["*"]` includes `DELETE` and `PATCH` — meaning a page served from 127.0.0.1:3210 can make destructive cross-origin requests to the production server if they happen to share an IP.
- **Fix:** Either remove the CORS middleware entirely for the Docker/production case (since frontend and backend are co-located), or scope it to dev-only via an environment variable: `allow_origins = os.environ.get("CORS_ORIGINS", "").split(",")` and leave it empty by default.

#### MOVE CARD POSITION IS OFF-BY-ONE WHEN REORDERING WITHIN SAME COLUMN
- **File:** `frontend/src/components/KanbanBoard.tsx:257-263`
- **Problem:** In `getMoveTarget`, when the drag target (`overId`) is a card rather than a column, the position is computed as the index of `overId` in `targetColumn.cardIds` *after filtering out `activeId`*. This is correct for cross-column moves. But for same-column reordering, the filtered index places the card *before* the target, which disagrees with the optimistic UI in `lib/kanban.ts:moveCard` which places it *at* the target index (splice-before). The two approaches produce the same visual result only when moving downward; moving a card upward within a column will persistently desynchronize the optimistic state from the server-confirmed state after the API responds.
- **Fix:** Decide on a single semantics ("insert before target" or "insert at target's position") and apply it consistently in both `getMoveTarget` and `database.move_card`. Add a backend test for same-column reorder (currently absent).

#### UNHANDLED `CARD_ID NOT IN BOARD` DURING AI MULTI-OPERATION SEQUENCES
- **File:** `backend/src/project_management_backend/board_ai.py:77-100`
- **Problem:** `validate_operations` builds `card_ids` from the board snapshot fetched once at the start of `handle_chat`. If the first AI operation is `create_card`, the new card's ID is assigned by the database at runtime — the AI cannot know it in advance. So if the AI emits `[create_card, edit_card(newCardId)]` in a single response, the edit will fail validation because `newCardId` is not in the snapshot. In practice gpt-4o-mini rarely generates this pattern, but it is architecturally unsound and will silently reject valid chained operations.
- **Fix:** Re-fetch the board state between operations (or update the in-memory snapshot after each mutation) so that validation against later operations reflects the state after earlier ones have committed.

---

### Medium

#### `COMPOSE.YAML` HAS NO VOLUME — DATABASE IS EPHEMERAL
- **File:** `compose.yaml:1-10`
- **Problem:** There is no `volumes:` declaration. Every `docker compose down` and `docker compose up` destroys all card and column data because the SQLite file lives inside the container's writable layer. Users will lose their board without warning.
- **Fix:** Add a named volume:
  ```yaml
  volumes:
    db-data:
  services:
    app:
      volumes:
        - db-data:/app/backend/data
  ```
  The `PROJECT_MANAGEMENT_DB_PATH` env var or the default `data/project-management.sqlite3` path already resolves inside `/app/backend`.

#### DOCKERFILE RUNS AS ROOT
- **File:** `Dockerfile:11-30`
- **Problem:** The runtime stage (`ghcr.io/astral-sh/uv:python3.12-bookworm-slim`) has no `USER` instruction, so uvicorn runs as root inside the container. If the process is ever exploited, the attacker has full container root.
- **Fix:** Add before the `CMD`:
  ```dockerfile
  RUN adduser --disabled-password --gecos "" appuser && \
      chown -R appuser /app
  USER appuser
  ```

#### `MOVE_CARD` IN DATABASE INSERTS THE CARD WITH `sort_order = insert_at` BEFORE RENUMBERING
- **File:** `backend/src/project_management_backend/database.py:306-331`
- **Problem:** On lines 306-321, the card is re-inserted with `sort_order = insert_at`. Then lines 323-331 renumber all cards including the one just inserted, overwriting `sort_order` again. The re-insert value is immediately discarded, which works correctly but is misleading and creates a redundant write. More importantly: `target_ids.insert(insert_at, card_id)` at line 303 inserts the card into the list *before* the renumbering loop. The loop then assigns each position correctly. However the card was already inserted at line 306 with its old `column_id` potentially still being the source column (for a cross-column move `card["column_id"]` is the source, but `column_id` passed in is the target). This is fine because `column_id` is the parameter — but the insert uses `card["board_id"]` and `card["created_at"]`, which is correct. No functional bug, but the logic is harder to follow than it needs to be.
- **Fix:** Minor: insert the card with `sort_order = insert_at` only as a placeholder, add a comment explaining the renumbering loop will correct it, or better, insert *after* building `target_ids` with a `sort_order` taken from `enumerate`. This is a code quality issue, not a correctness bug.

#### CONVERSATION HISTORY GROWS UNBOUNDEDLY
- **File:** `frontend/src/components/AiChatSidebar.tsx:39`
- **Problem:** Every AI chat message is appended to `messages` state and the full history is sent to the backend on every request: `const history = messages.map(...)`. After 20-30 exchanges the context window fills up and OpenAI will return a `context_length_exceeded` error, which surfaces to the user as "Unable to reach the AI assistant" with no further detail.
- **Fix:** Cap the history sent to the API (e.g., keep the last 10 message pairs): `const history = messages.slice(-20).map(...)`. Optionally add a "Clear conversation" button. On the backend, the OpenAI error should be caught specifically and returned with a more helpful message like "Conversation too long — please start a new chat."

#### `HANDLEADDCARD` SILENTLY SUBSTITUTES EMPTY DETAILS
- **File:** `frontend/src/components/KanbanBoard.tsx:103-105`
- **Problem:** `api.createCard(columnId, title, details || "No details yet.")` — if the user intentionally leaves the details field blank, the backend stores "No details yet." This behavior is invisible to the user and pollutes cards with placeholder text. The backend schema already accepts `details: str = ""` (empty string is valid).
- **Fix:** Remove the `|| "No details yet."` fallback. Pass `details` as-is (empty string is fine).

#### MESSAGE KEY USING INDEX IS FRAGILE
- **File:** `frontend/src/components/AiChatSidebar.tsx:116`
- **Problem:** `key={\`${message.role}-${index}\`}` — using array index as part of a React key means React will re-use DOM nodes incorrectly if messages are ever removed (e.g., on clear). Since messages are only appended this doesn't cause a bug today, but it is an anti-pattern that will break if a "clear conversation" feature is added.
- **Fix:** Generate a stable ID when appending each message: `id: crypto.randomUUID()` added to `DisplayMessage`, used as `key={message.id}`.

#### OPTIMISTIC DRAG STATE NOT APPLIED — VISUAL JANK ON SLOW NETWORKS
- **File:** `frontend/src/components/KanbanBoard.tsx:80-96`
- **Problem:** `handleDragEnd` calls `applyBoardUpdate(() => api.moveCard(...))` which awaits the API response before updating `board` state. During the round-trip, dnd-kit has already reset the dragged item to its original position (because `board.columns` has not changed). The card visually snaps back, then jumps to the new position when the response arrives. The `lib/kanban.ts:moveCard` function exists and is tested but is never used in `KanbanBoard`.
- **Fix:** Apply the optimistic update with `lib/kanban.ts:moveCard` immediately in `handleDragEnd` (update `board` state before the API call), then replace it with the server response when it arrives. On error, revert to the previous board state.

#### BACKEND TESTS MISSING FOR `DELETE_CARD` SORT-ORDER NORMALIZATION
- **File:** `backend/tests/test_app.py:322-329`
- **Problem:** `test_delete_card_removes_it_from_board` confirms the card is removed but does not verify that `normalize_column_order` ran correctly — i.e., it does not assert that remaining card `sort_order` values are contiguous starting from 0. If `normalize_column_order` silently failed, this test would still pass.
- **Fix:** After deleting `card-1` from backlog, fetch the board and assert that `card-2` is still at index 0 in `cardIds`. Then also test deleting a middle card: assert the remaining cards are `[card-1]` (not `[card-1, <gap>]`).

#### NO BACKEND VALIDATION ON STRING LENGTH FOR TITLE/DETAILS
- **File:** `backend/src/project_management_backend/schemas.py:26-38`
- **Problem:** `RenameColumnRequest.title`, `CreateCardRequest.title`, and `UpdateCardRequest.title` all have `min_length=1` but no `max_length`. A client can send a title of several megabytes, which SQLite will happily store. This inflates the database and is returned in every `GET /api/board` response.
- **Fix:** Add `max_length=500` (or similar) to all title and details fields in the Pydantic schemas. No migration required — it is a validation-layer constraint.

---

### Low

#### `INITIALDATA` IN `KANBAN.TS` IS STALE FALLBACK THAT MISLEADS TESTS
- **File:** `frontend/src/lib/kanban.ts:18-72`
- **Problem:** `initialData` is a hardcoded copy of the seed data. It is imported in tests (`api.test.ts`, `KanbanBoard.test.tsx`, `ProjectApp.test.tsx`) as the mock server response. This is fine, but it means tests implicitly depend on the seed data never changing. If a new card is added to the backend seed, tests that rely on `columns[0].cardIds == ["card-1", "card-2"]` will silently pass against stale data.
- **Fix:** Low priority, but consider removing `initialData` from `kanban.ts` (it has no runtime use) and defining test fixtures directly in the test files so the dependency is explicit.

#### `CREATEID` IN `KANBAN.TS` IS UNUSED
- **File:** `frontend/src/lib/kanban.ts:164-168`
- **Problem:** `createId` generates a client-side random ID. It was presumably used in an earlier purely-frontend version. Today all IDs are generated by the backend (`database.py:241`). The function is exported but never imported anywhere.
- **Fix:** Delete the function.

#### PLAYWRIGHT TEST SHARES MUTABLE DATABASE ACROSS TESTS IN A RUN
- **File:** `frontend/playwright.config.ts:14-16`
- **Problem:** The playwright database is initialized by running `rm -f ../data/playwright.sqlite3` only once when the backend server starts, not between individual tests. Tests that mutate data (add card, rename column) leave state that affects later tests. For example, `test("adds a card to a column")` adds "Playwright card" which will appear in subsequent tests that load the same board.
- **Fix:** Either reset the database between tests by calling a `DELETE FROM cards WHERE id NOT IN (...)` endpoint, or make each test use its own isolated database by using `playwright test --workers 1` with a `beforeEach` API reset, or add an explicit `/api/reset` endpoint (dev-only) that re-seeds.

#### PLAYWRIGHT DRAG TEST USES MAGIC PIXEL OFFSET
- **File:** `frontend/tests/kanban.spec.ts:65`
- **Problem:** `columnBox.y + 120` is a hardcoded pixel offset to position the drop target. This is fragile across viewport sizes, zoom levels, or if the column layout changes.
- **Fix:** Compute the drop position from `columnBox.y + columnBox.height / 2`, or use dnd-kit's keyboard drag testing which is more deterministic.

#### `APIBORDERDATA` RESPONSE NEVER INCLUDES `ID` FIELD BUT BOARDRESPONSE REQUIRES IT
- **File:** `frontend/src/lib/kanban.ts:13-16` and `backend/src/project_management_backend/schemas.py:18-22`
- **Problem:** `BoardData` in the frontend is `{ columns, cards }` (no `id` or `title`). `BoardResponse` on the backend includes `id` and `title`. The API returns `id` and `title` but the frontend silently drops them. This is not a bug (the frontend doesn't need them) but it means the TypeScript type is incomplete — future code that tries to display `board.title` dynamically would find it missing and get a type error.
- **Fix:** Either add `id: string; title: string` to `BoardData` in `kanban.ts`, or document why they are intentionally omitted.

#### COLUMN TITLE INPUT HAS NO `KEY` TIED TO COLUMN DATA
- **File:** `frontend/src/components/KanbanColumn.tsx:60-65`
- **Problem:** The column title `<input defaultValue={column.title}>` uses `defaultValue` (uncontrolled). If the board is replaced with a server response that changes column titles (e.g., after an AI rename), React will not update the input because `defaultValue` only sets the initial value. The input will show the stale title until the user navigates away or the component unmounts.
- **Fix:** Add `key={column.title}` to the `<input>` to force a remount when the title changes from an external update, or switch to a controlled input with local state initialized from `column.title` and reset via `useEffect` when the prop changes.

#### NO `ARIA-LIVE` OR LOADING INDICATOR ON BOARD MUTATION OPERATIONS
- **File:** `frontend/src/components/KanbanBoard.tsx:66-74`
- **Problem:** `applyBoardUpdate` performs async API calls but provides no loading state beyond the generic error message. The user gets no feedback that their rename/delete/add is in flight, and there is no way to know if a silent failure occurred without watching for the error banner.
- **Fix:** Add a per-operation loading state or a subtle spinner. At minimum, disable the triggering UI element during the in-flight request to prevent double-submit. Low priority for an MVP but worth noting.

---

## What's Done Well

- **No SQL injection surface.** Every database query in `database.py` uses parameterized `?` placeholders without exception. No string formatting is used in SQL construction.
- **Board ID is always scoped.** Every read and write query filters on `board_id = DEFAULT_BOARD_ID`. There is no way to read or mutate another user's data even if additional users existed in the database.
- **Structured AI output with schema enforcement.** Using OpenAI's `json_schema` response format with `strict: true` and validating the result through Pydantic means the AI cannot produce arbitrary SQL or execute operations outside the allowed set.
- **AI validation is pre-flight and total.** `validate_operations` rejects the entire batch before any mutation if any single operation is invalid. The test `test_ai_chat_rejects_invalid_operation_without_changing_board` verifies this contract end-to-end.
- **TypeScript strict mode is on.** `tsconfig.json` has `"strict": true`. Combined with well-typed API response shapes, this catches most category errors at compile time.
- **Test isolation is solid on the backend.** Each pytest fixture creates a fresh SQLite file in `tmp_path` and uses `TestClient` with full lifespan, ensuring tests never share state.
- **`isMounted` guard on the fetch effect.** `KanbanBoard.tsx` correctly prevents state updates after unmount with a closure-captured `isMounted` flag, avoiding the classic React stale-closure warning.
- **Docker build is lean and multi-stage.** The frontend builder stage is discarded; only the static `out/` is copied into the runtime image. The `uv sync --frozen --no-dev` pattern ensures reproducible, dependency-minimal containers.
- **The `.env` file is correctly gitignored and excluded from `.dockerignore`.** The git history shows it was never committed.

---

## Recommended Action Order

1. **Rotate the OpenAI API key** (`sk-proj-...` in `.env`) immediately — treat it as compromised. This takes 30 seconds in the OpenAI dashboard and eliminates the only live security risk.

2. **Add a Docker volume for the SQLite database** (`compose.yaml`) — without this, every restart silently destroys all user data. One-line fix.

3. **Wrap AI multi-operation execution in a transaction** (`board_ai.py:apply_operations`) — prevents partial board mutations when a second or third operation fails mid-batch.

4. **Add a non-root user to the Dockerfile** — straightforward 3-line addition; eliminates container root execution.

5. **Cap the conversation history sent to OpenAI** (`AiChatSidebar.tsx`) — prevents context-length errors from degrading the AI feature silently.

6. **Fix the optimistic drag-drop state** (`KanbanBoard.tsx:handleDragEnd`) — apply `lib/kanban.ts:moveCard` immediately on drag end rather than waiting for the API response; the helper already exists and is tested.

7. **Apply `max_length` constraints to Pydantic title/details fields** (`schemas.py`) — protects against oversized payloads inflating the database and every board response.

8. **Fix the column title input stale-value bug** (`KanbanColumn.tsx`) — add `key={column.title}` to the uncontrolled input so external renames (from AI) are reflected correctly.

9. **Remove the `|| "No details yet."` details fallback** (`KanbanBoard.tsx:103`) — the substitution is invisible to users and stores unwanted text.

10. **Delete the unused `createId` export** (`kanban.ts:164`) and consider removing `initialData` from the library file to prevent tests from silently depending on seed-data stability.
