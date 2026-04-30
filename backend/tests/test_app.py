from fastapi.testclient import TestClient
import pytest

from project_management_backend import ai
from project_management_backend.schemas import AiBoardOperation, AiStructuredOutput
import project_management_backend.main as backend_main
from project_management_backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PROJECT_MANAGEMENT_DB_PATH", str(tmp_path / "app.sqlite3"))
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_returns_json(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "project-management",
    }


def test_ai_connectivity_returns_mocked_openai_answer(client, monkeypatch) -> None:
    monkeypatch.setattr(ai, "check_connectivity", lambda: "4")

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 200
    assert response.json() == {
        "model": "gpt-4o-mini",
        "prompt": "What is 2+2? Reply with only the number.",
        "answer": "4",
    }


def test_ai_connectivity_reports_missing_api_key(client, monkeypatch) -> None:
    def raise_missing_key() -> str:
        raise ai.MissingApiKeyError("OPENAI_API_KEY is not configured.")

    monkeypatch.setattr(ai, "check_connectivity", raise_missing_key)

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENAI_API_KEY is not configured."


def test_parse_structured_ai_response() -> None:
    parsed = ai.parse_structured_output(
        """
        {
          "message": "I created the card.",
          "operations": [
            {
              "type": "create_card",
              "cardId": null,
              "columnId": "col-backlog",
              "title": "New task",
              "details": "Task details",
              "position": null
            }
          ]
        }
        """
    )

    assert parsed.message == "I created the card."
    assert parsed.operations[0].type == "create_card"
    assert parsed.operations[0].columnId == "col-backlog"


def test_parse_structured_ai_response_falls_back_for_empty_message() -> None:
    parsed = ai.parse_structured_output(
        """
        {
          "message": "",
          "operations": []
        }
        """
    )

    assert parsed.message == "Done."
    assert parsed.operations == []


def test_ai_chat_returns_no_op_answer(client, monkeypatch) -> None:
    monkeypatch.setattr(
        ai,
        "chat_about_board",
        lambda **kwargs: AiStructuredOutput(message="The board looks good.", operations=[]),
    )

    response = client.post(
        "/api/ai/chat",
        json={
            "question": "What should I work on?",
            "history": [{"role": "user", "content": "Hi"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "The board looks good."
    assert body["appliedUpdates"] == []
    assert body["board"]["columns"][0]["cardIds"] == ["card-1", "card-2"]


def test_ai_chat_creates_card(client, monkeypatch) -> None:
    monkeypatch.setattr(
        ai,
        "chat_about_board",
        lambda **kwargs: AiStructuredOutput(
            message="I added a planning card.",
            operations=[
                AiBoardOperation(
                    type="create_card",
                    columnId="col-backlog",
                    title="Plan launch",
                    details="Draft launch checklist.",
                )
            ],
        ),
    )

    response = client.post("/api/ai/chat", json={"question": "Add launch planning."})

    assert response.status_code == 200
    body = response.json()
    new_card_id = body["board"]["columns"][0]["cardIds"][-1]
    assert body["appliedUpdates"] == [
        {"type": "create_card", "summary": "Created card 'Plan launch'."}
    ]
    assert body["board"]["cards"][new_card_id]["title"] == "Plan launch"
    assert client.get("/api/board").json()["cards"][new_card_id]["title"] == "Plan launch"


def test_ai_chat_edits_card(client, monkeypatch) -> None:
    monkeypatch.setattr(
        ai,
        "chat_about_board",
        lambda **kwargs: AiStructuredOutput(
            message="I clarified the first card.",
            operations=[
                AiBoardOperation(
                    type="edit_card",
                    cardId="card-1",
                    title="Align roadmap and metrics",
                    details="Draft themes with measurable outcomes.",
                )
            ],
        ),
    )

    response = client.post("/api/ai/chat", json={"question": "Clarify card 1."})

    assert response.status_code == 200
    card = response.json()["board"]["cards"]["card-1"]
    assert card["title"] == "Align roadmap and metrics"
    assert card["details"] == "Draft themes with measurable outcomes."


def test_ai_chat_moves_card(client, monkeypatch) -> None:
    monkeypatch.setattr(
        ai,
        "chat_about_board",
        lambda **kwargs: AiStructuredOutput(
            message="I moved the roadmap card to review.",
            operations=[
                AiBoardOperation(
                    type="move_card",
                    cardId="card-1",
                    columnId="col-review",
                    position=0,
                )
            ],
        ),
    )

    response = client.post("/api/ai/chat", json={"question": "Move card 1 to review."})

    assert response.status_code == 200
    body = response.json()["board"]
    backlog = next(column for column in body["columns"] if column["id"] == "col-backlog")
    review = next(column for column in body["columns"] if column["id"] == "col-review")
    assert backlog["cardIds"] == ["card-2"]
    assert review["cardIds"] == ["card-1", "card-6"]


def test_ai_chat_rejects_invalid_operation_without_changing_board(client, monkeypatch) -> None:
    before = client.get("/api/board").json()
    monkeypatch.setattr(
        ai,
        "chat_about_board",
        lambda **kwargs: AiStructuredOutput(
            message="I tried to move a card.",
            operations=[
                AiBoardOperation(
                    type="move_card",
                    cardId="missing-card",
                    columnId="col-review",
                    position=0,
                )
            ],
        ),
    )

    response = client.post("/api/ai/chat", json={"question": "Move a missing card."})

    assert response.status_code == 502
    assert client.get("/api/board").json() == before


def test_index_serves_frontend_entrypoint(client, tmp_path, monkeypatch) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(backend_main, "STATIC_DIR", static_dir.resolve())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Kanban Studio" in response.text


def test_static_asset_serves_exported_files(client, tmp_path, monkeypatch) -> None:
    static_dir = tmp_path / "static"
    asset_dir = static_dir / "_next" / "static"
    asset_dir.mkdir(parents=True)
    (asset_dir / "app.js").write_text("console.log('kanban');", encoding="utf-8")
    monkeypatch.setattr(backend_main, "STATIC_DIR", static_dir.resolve())

    response = client.get("/_next/static/app.js")

    assert response.status_code == 200
    assert "console.log('kanban');" in response.text


def test_database_initializes_and_seeds_default_board(client, tmp_path) -> None:
    response = client.get("/api/board")

    assert (tmp_path / "app.sqlite3").is_file()
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "board-1"
    assert body["title"] == "Kanban Studio"
    assert [column["id"] for column in body["columns"]] == [
        "col-backlog",
        "col-discovery",
        "col-progress",
        "col-review",
        "col-done",
    ]
    assert body["columns"][0]["cardIds"] == ["card-1", "card-2"]
    assert body["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_rename_column_persists(client) -> None:
    response = client.patch("/api/columns/col-backlog", json={"title": "Ideas"})

    assert response.status_code == 200
    assert response.json()["columns"][0]["title"] == "Ideas"
    assert client.get("/api/board").json()["columns"][0]["title"] == "Ideas"


def test_create_card_adds_it_to_column_end(client) -> None:
    response = client.post(
        "/api/cards",
        json={
            "columnId": "col-backlog",
            "title": "Persisted card",
            "details": "Created through the API.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    backlog = body["columns"][0]
    new_card_id = backlog["cardIds"][-1]
    assert body["cards"][new_card_id] == {
        "id": new_card_id,
        "title": "Persisted card",
        "details": "Created through the API.",
    }


def test_update_card_changes_title_and_details(client) -> None:
    response = client.patch(
        "/api/cards/card-1",
        json={"title": "Updated title", "details": "Updated details"},
    )

    assert response.status_code == 200
    assert response.json()["cards"]["card-1"] == {
        "id": "card-1",
        "title": "Updated title",
        "details": "Updated details",
    }


def test_move_card_to_another_column_and_position(client) -> None:
    response = client.post(
        "/api/cards/card-1/move",
        json={"columnId": "col-review", "position": 0},
    )

    assert response.status_code == 200
    body = response.json()
    backlog = next(column for column in body["columns"] if column["id"] == "col-backlog")
    review = next(column for column in body["columns"] if column["id"] == "col-review")
    assert backlog["cardIds"] == ["card-2"]
    assert review["cardIds"] == ["card-1", "card-6"]


def test_delete_card_removes_it_from_board(client) -> None:
    response = client.delete("/api/cards/card-1")

    assert response.status_code == 200
    body = response.json()
    backlog = next(column for column in body["columns"] if column["id"] == "col-backlog")
    assert backlog["cardIds"] == ["card-2"]
    assert "card-1" not in body["cards"]


def test_delete_card_normalizes_sort_order(client) -> None:
    # Backlog starts with [card-1, card-2]. Delete card-1 (index 0).
    client.delete("/api/cards/card-1")

    board = client.get("/api/board").json()
    backlog = next(col for col in board["columns"] if col["id"] == "col-backlog")
    # card-2 must now be at index 0 with no gaps
    assert backlog["cardIds"] == ["card-2"]

    # Add a card, then delete the first one again to confirm contiguous ordering
    client.post("/api/cards", json={"columnId": "col-backlog", "title": "Extra", "details": ""})
    board = client.get("/api/board").json()
    backlog = next(col for col in board["columns"] if col["id"] == "col-backlog")
    first_id, second_id = backlog["cardIds"]

    client.delete(f"/api/cards/{first_id}")
    board = client.get("/api/board").json()
    backlog = next(col for col in board["columns"] if col["id"] == "col-backlog")
    assert backlog["cardIds"] == [second_id]


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("patch", "/api/columns/missing-column", {"title": "Nope"}),
        ("post", "/api/cards", {"columnId": "missing-column", "title": "Nope"}),
        ("patch", "/api/cards/missing-card", {"title": "Nope", "details": ""}),
        ("post", "/api/cards/card-1/move", {"columnId": "missing-column", "position": 0}),
        ("delete", "/api/cards/missing-card", None),
    ],
)
def test_invalid_ids_return_404(client, method, path, json) -> None:
    if json is None:
        response = getattr(client, method)(path)
    else:
        response = getattr(client, method)(path, json=json)

    assert response.status_code == 404


def test_malformed_requests_return_422(client) -> None:
    response = client.post(
        "/api/cards",
        json={"columnId": "col-backlog", "title": ""},
    )

    assert response.status_code == 422
