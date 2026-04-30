# Database Approach

The MVP should use a local SQLite database created automatically when the backend starts. The proposed schema is saved in `docs/DATABASE_SCHEMA.json`.

## Goals

- Persist the current Kanban board shape: ordered columns, ordered cards, editable column titles, card title/details.
- Support the MVP limitation of one signed-in user and one board per user.
- Keep the schema ready for future multi-user support without adding real authentication yet.
- Keep implementation simple and local-first.

## Database File

Use SQLite at `data/project-management.sqlite3` by default. The backend should create the `data/` directory and database file if they do not exist. Runtime database files should not be committed.

## Tables

`users`
- Stores users by stable text ID.
- The MVP seeds one user with username `user`.
- No password is stored for the MVP because Part 4 sign-in is local-only and hardcoded.

`boards`
- Stores boards owned by users.
- The MVP enforces one board per user with a unique index on `user_id`.

`board_columns`
- Stores the five fixed columns for each board.
- `column_key` identifies the fixed column slot: `backlog`, `discovery`, `in_progress`, `review`, `done`.
- `title` is mutable, so users can rename columns without changing the fixed column identity.
- `sort_order` preserves display order. For the MVP, columns should not be created, deleted, or reordered through the UI.

`cards`
- Stores cards for a board and their current column.
- `column_id` points to the current column.
- `sort_order` preserves card order inside a column.
- Moving a card updates its `column_id` and recalculates affected `sort_order` values.

## Initialization

On backend startup or first database access:

1. Create the SQLite database if it does not exist.
2. Enable foreign keys with `PRAGMA foreign_keys = ON`.
3. Create tables and indexes if they do not exist.
4. Seed the MVP user, one board, five columns, and the current demo cards when the database is empty.
5. Keep seed operations idempotent so repeated starts do not duplicate data.

## Migrations

For the MVP, use a simple schema-version table or metadata value when implementing the backend. Version `1` should match `docs/DATABASE_SCHEMA.json`.

Future migrations should run at startup before serving API requests. Each migration should be idempotent and covered by backend tests.

## Frontend Payload Shape

The backend should return the board in the shape the current frontend already understands:

```json
{
  "id": "board-1",
  "title": "Kanban Studio",
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

The database can stay normalized while the API assembles this response for the frontend.

## Expected API Operations

Part 6 should add backend routes that support:

- Read the current MVP user's board.
- Rename a column by ID.
- Create a card in a column.
- Update a card's title and details.
- Move a card to a new column and position.
- Delete a card.

All operations should be scoped to the current MVP user and board, even though real authentication is not yet implemented.

## Out Of Scope For This Phase

- Real password storage.
- Multiple boards per user.
- Column create/delete/reorder.
- AI conversation persistence.
- Production-grade migration tooling.
