import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAIError
from project_management_backend import ai
from project_management_backend import database
from project_management_backend.schemas import (
    AiConnectivityResponse,
    BoardResponse,
    CreateCardRequest,
    MoveCardRequest,
    RenameColumnRequest,
    UpdateCardRequest,
)

STATIC_DIR = Path(os.environ.get("APP_STATIC_DIR", Path(__file__).parent / "static")).resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Project Management MVP", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3210", "http://localhost:3210"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "project-management"}


@app.post("/api/ai/connectivity", response_model=AiConnectivityResponse)
def check_ai_connectivity() -> dict[str, str]:
    try:
        answer = ai.check_connectivity()
    except ai.MissingApiKeyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except OpenAIError as error:
        raise HTTPException(status_code=502, detail="OpenAI request failed.") from error

    return {
        "model": ai.AI_MODEL,
        "prompt": ai.CONNECTIVITY_PROMPT,
        "answer": answer,
    }


@app.get("/api/board", response_model=BoardResponse)
def read_board() -> dict:
    try:
        return database.get_board()
    except database.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.patch("/api/columns/{column_id}", response_model=BoardResponse)
def rename_column(
    column_id: str,
    request: Annotated[RenameColumnRequest, Body()],
) -> dict:
    try:
        return database.rename_column(column_id, request.title)
    except database.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/cards", response_model=BoardResponse, status_code=201)
def create_card(request: Annotated[CreateCardRequest, Body()]) -> dict:
    try:
        return database.create_card(request.columnId, request.title, request.details)
    except database.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.patch("/api/cards/{card_id}", response_model=BoardResponse)
def update_card(
    card_id: str,
    request: Annotated[UpdateCardRequest, Body()],
) -> dict:
    try:
        return database.update_card(card_id, request.title, request.details)
    except database.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/cards/{card_id}/move", response_model=BoardResponse)
def move_card(
    card_id: str,
    request: Annotated[MoveCardRequest, Body()],
) -> dict:
    try:
        return database.move_card(card_id, request.columnId, request.position)
    except database.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/cards/{card_id}", response_model=BoardResponse)
def delete_card(card_id: str) -> dict:
    try:
        return database.delete_card(card_id)
    except database.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


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
