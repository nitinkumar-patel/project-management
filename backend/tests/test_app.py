from fastapi.testclient import TestClient

import project_management_backend.main as backend_main
from project_management_backend.main import app

client = TestClient(app)


def test_health_check_returns_json() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "project-management",
    }


def test_index_serves_frontend_entrypoint(tmp_path, monkeypatch) -> None:
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


def test_static_asset_serves_exported_files(tmp_path, monkeypatch) -> None:
    static_dir = tmp_path / "static"
    asset_dir = static_dir / "_next" / "static"
    asset_dir.mkdir(parents=True)
    (asset_dir / "app.js").write_text("console.log('kanban');", encoding="utf-8")
    monkeypatch.setattr(backend_main, "STATIC_DIR", static_dir.resolve())

    response = client.get("/_next/static/app.js")

    assert response.status_code == 200
    assert "console.log('kanban');" in response.text
