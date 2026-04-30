from fastapi.testclient import TestClient
import pytest

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
