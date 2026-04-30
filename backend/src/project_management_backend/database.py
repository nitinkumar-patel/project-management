import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

DEFAULT_USER_ID = "user-1"
DEFAULT_BOARD_ID = "board-1"


class NotFoundError(Exception):
    pass


def get_database_path() -> Path:
    return Path(os.environ.get("PROJECT_MANAGEMENT_DB_PATH", "data/project-management.sqlite3"))


def connect() -> sqlite3.Connection:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS boards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_boards_one_per_user
                ON boards(user_id);

            CREATE TABLE IF NOT EXISTS board_columns (
                id TEXT PRIMARY KEY,
                board_id TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
                column_key TEXT NOT NULL,
                title TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_board_columns_board_order
                ON board_columns(board_id, sort_order);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_board_columns_board_key
                ON board_columns(board_id, column_key);

            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                board_id TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
                column_id TEXT NOT NULL REFERENCES board_columns(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_cards_board_id
                ON cards(board_id);

            CREATE INDEX IF NOT EXISTS idx_cards_column_order
                ON cards(column_id, sort_order);
            """
        )
        connection.execute(
            """
            INSERT INTO schema_metadata (key, value)
            VALUES ('schema_version', '1')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """
        )
        seed_default_board(connection)


def seed_default_board(connection: sqlite3.Connection) -> None:
    existing_board = connection.execute(
        "SELECT id FROM boards WHERE id = ?", (DEFAULT_BOARD_ID,)
    ).fetchone()
    if existing_board:
        return

    now = utc_now()
    connection.execute(
        """
        INSERT INTO users (id, username, display_name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(username) DO NOTHING
        """,
        (DEFAULT_USER_ID, "user", "MVP User", now, now),
    )
    connection.execute(
        """
        INSERT INTO boards (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (DEFAULT_BOARD_ID, DEFAULT_USER_ID, "Kanban Studio", now, now),
    )

    columns = [
        ("col-backlog", "backlog", "Backlog", 0),
        ("col-discovery", "discovery", "Discovery", 1),
        ("col-progress", "in_progress", "In Progress", 2),
        ("col-review", "review", "Review", 3),
        ("col-done", "done", "Done", 4),
    ]
    connection.executemany(
        """
        INSERT INTO board_columns
            (id, board_id, column_key, title, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (column_id, DEFAULT_BOARD_ID, column_key, title, sort_order, now, now)
            for column_id, column_key, title, sort_order in columns
        ],
    )

    cards = [
        ("card-1", "col-backlog", "Align roadmap themes", "Draft quarterly themes with impact statements and metrics.", 0),
        ("card-2", "col-backlog", "Gather customer signals", "Review support tags, sales notes, and churn feedback.", 1),
        ("card-3", "col-discovery", "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs.", 0),
        ("card-4", "col-progress", "Refine status language", "Standardize column labels and tone across the board.", 0),
        ("card-5", "col-progress", "Design card layout", "Add hierarchy and spacing for scanning dense lists.", 1),
        ("card-6", "col-review", "QA micro-interactions", "Verify hover, focus, and loading states.", 0),
        ("card-7", "col-done", "Ship marketing page", "Final copy approved and asset pack delivered.", 0),
        ("card-8", "col-done", "Close onboarding sprint", "Document release notes and share internally.", 1),
    ]
    connection.executemany(
        """
        INSERT INTO cards
            (id, board_id, column_id, title, details, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (card_id, DEFAULT_BOARD_ID, column_id, title, details, sort_order, now, now)
            for card_id, column_id, title, details, sort_order in cards
        ],
    )


def get_board() -> dict:
    with connect() as connection:
        board = connection.execute(
            "SELECT id, title FROM boards WHERE id = ?", (DEFAULT_BOARD_ID,)
        ).fetchone()
        if not board:
            raise NotFoundError("Board not found.")

        columns = connection.execute(
            """
            SELECT id, title
            FROM board_columns
            WHERE board_id = ?
            ORDER BY sort_order
            """,
            (DEFAULT_BOARD_ID,),
        ).fetchall()
        cards = connection.execute(
            """
            SELECT id, column_id, title, details
            FROM cards
            WHERE board_id = ?
            ORDER BY column_id, sort_order
            """,
            (DEFAULT_BOARD_ID,),
        ).fetchall()

    cards_by_column: dict[str, list[str]] = {column["id"]: [] for column in columns}
    cards_by_id = {}
    for card in cards:
        cards_by_column.setdefault(card["column_id"], []).append(card["id"])
        cards_by_id[card["id"]] = {
            "id": card["id"],
            "title": card["title"],
            "details": card["details"],
        }

    return {
        "id": board["id"],
        "title": board["title"],
        "columns": [
            {
                "id": column["id"],
                "title": column["title"],
                "cardIds": cards_by_column.get(column["id"], []),
            }
            for column in columns
        ],
        "cards": cards_by_id,
    }


def rename_column(column_id: str, title: str) -> dict:
    now = utc_now()
    with connect() as connection:
        cursor = connection.execute(
            """
            UPDATE board_columns
            SET title = ?, updated_at = ?
            WHERE id = ? AND board_id = ?
            """,
            (title, now, column_id, DEFAULT_BOARD_ID),
        )
        if cursor.rowcount == 0:
            raise NotFoundError("Column not found.")

    return get_board()


def create_card(column_id: str, title: str, details: str) -> dict:
    with connect() as connection:
        _create_card(connection, column_id, title, details)
    return get_board()


def update_card(card_id: str, title: str, details: str) -> dict:
    with connect() as connection:
        _update_card(connection, card_id, title, details)
    return get_board()


def delete_card(card_id: str) -> dict:
    with connect() as connection:
        card = get_card_row(connection, card_id)
        connection.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        normalize_column_order(connection, card["column_id"])
    return get_board()


def move_card(card_id: str, column_id: str, position: int) -> dict:
    with connect() as connection:
        _move_card(connection, card_id, column_id, position)
    return get_board()


def ensure_column_exists(connection: sqlite3.Connection, column_id: str) -> None:
    column = connection.execute(
        "SELECT id FROM board_columns WHERE id = ? AND board_id = ?",
        (column_id, DEFAULT_BOARD_ID),
    ).fetchone()
    if not column:
        raise NotFoundError("Column not found.")


def get_card_row(connection: sqlite3.Connection, card_id: str) -> sqlite3.Row:
    card = connection.execute(
        "SELECT * FROM cards WHERE id = ? AND board_id = ?",
        (card_id, DEFAULT_BOARD_ID),
    ).fetchone()
    if not card:
        raise NotFoundError("Card not found.")
    return card


def next_card_order(connection: sqlite3.Connection, column_id: str) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM cards WHERE column_id = ?",
        (column_id,),
    ).fetchone()
    return int(row["next_order"])


def normalize_column_order(connection: sqlite3.Connection, column_id: str) -> None:
    rows = connection.execute(
        "SELECT id FROM cards WHERE column_id = ? ORDER BY sort_order",
        (column_id,),
    ).fetchall()
    now = utc_now()
    for sort_order, row in enumerate(rows):
        connection.execute(
            "UPDATE cards SET sort_order = ?, updated_at = ? WHERE id = ?",
            (sort_order, now, row["id"]),
        )


def _create_card(connection: sqlite3.Connection, column_id: str, title: str, details: str) -> str:
    now = utc_now()
    card_id = f"card-{uuid4().hex[:12]}"
    ensure_column_exists(connection, column_id)
    next_order = next_card_order(connection, column_id)
    connection.execute(
        """
        INSERT INTO cards
            (id, board_id, column_id, title, details, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (card_id, DEFAULT_BOARD_ID, column_id, title, details, next_order, now, now),
    )
    return card_id


def _update_card(connection: sqlite3.Connection, card_id: str, title: str, details: str) -> None:
    now = utc_now()
    cursor = connection.execute(
        """
        UPDATE cards
        SET title = ?, details = ?, updated_at = ?
        WHERE id = ? AND board_id = ?
        """,
        (title, details, now, card_id, DEFAULT_BOARD_ID),
    )
    if cursor.rowcount == 0:
        raise NotFoundError("Card not found.")


def _move_card(connection: sqlite3.Connection, card_id: str, column_id: str, position: int) -> None:
    card = get_card_row(connection, card_id)
    ensure_column_exists(connection, column_id)

    source_column_id = card["column_id"]
    connection.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    normalize_column_order(connection, source_column_id)

    target_cards = connection.execute(
        """
        SELECT id
        FROM cards
        WHERE column_id = ?
        ORDER BY sort_order
        """,
        (column_id,),
    ).fetchall()
    target_ids = [row["id"] for row in target_cards]
    insert_at = min(position, len(target_ids))
    target_ids.insert(insert_at, card_id)

    now = utc_now()
    connection.execute(
        """
        INSERT INTO cards
            (id, board_id, column_id, title, details, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            card["id"],
            card["board_id"],
            column_id,
            card["title"],
            card["details"],
            insert_at,
            card["created_at"],
            now,
        ),
    )
    for sort_order, target_card_id in enumerate(target_ids):
        connection.execute(
            """
            UPDATE cards
            SET sort_order = ?, updated_at = ?
            WHERE id = ?
            """,
            (sort_order, now, target_card_id),
        )
