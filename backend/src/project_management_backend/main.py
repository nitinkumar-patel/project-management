import os
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse

STATIC_DIR = Path(
    os.environ.get("APP_STATIC_DIR", Path(__file__).parent / "static")
).resolve()

app = FastAPI(title="Project Management MVP")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "project-management"}


@app.get("/", response_class=FileResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{asset_path:path}", response_class=FileResponse)
def static_asset(asset_path: str) -> FileResponse:
    file_path = (STATIC_DIR / asset_path).resolve()

    try:
        file_path.relative_to(STATIC_DIR)
    except ValueError as error:
        raise HTTPException(status_code=404) from error

    if not file_path.is_file():
        raise HTTPException(status_code=404)

    return FileResponse(file_path)
