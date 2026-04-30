from fastapi.testclient import TestClient

from project_management_backend.main import app

client = TestClient(app)


def test_health_check_returns_json() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "project-management",
    }


def test_index_serves_scaffold_html() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Hello from the Project Management MVP" in response.text
    assert 'fetch("/api/health")' in response.text
