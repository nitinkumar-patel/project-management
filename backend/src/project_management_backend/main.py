from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Project Management MVP")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "project-management"}


@app.get("/", response_class=FileResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
