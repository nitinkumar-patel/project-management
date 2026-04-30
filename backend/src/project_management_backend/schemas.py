from typing import Literal

from pydantic import BaseModel, Field


class CardResponse(BaseModel):
    id: str
    title: str
    details: str


class ColumnResponse(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardResponse(BaseModel):
    id: str
    title: str
    columns: list[ColumnResponse]
    cards: dict[str, CardResponse]


class RenameColumnRequest(BaseModel):
    title: str = Field(min_length=1)


class CreateCardRequest(BaseModel):
    columnId: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str = ""


class UpdateCardRequest(BaseModel):
    title: str = Field(min_length=1)
    details: str = ""


class MoveCardRequest(BaseModel):
    columnId: str = Field(min_length=1)
    position: int = Field(ge=0)


class AiConnectivityResponse(BaseModel):
    model: str
    prompt: str
    answer: str


class AiChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AiChatRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[AiChatMessage] = []


class AiBoardOperation(BaseModel):
    type: Literal["create_card", "edit_card", "move_card"]
    cardId: str | None = None
    columnId: str | None = None
    title: str | None = None
    details: str | None = None
    position: int | None = Field(default=None, ge=0)


class AiStructuredOutput(BaseModel):
    message: str = Field(min_length=1)
    operations: list[AiBoardOperation] = []


class AppliedAiUpdate(BaseModel):
    type: str
    summary: str


class AiChatResponse(BaseModel):
    message: str
    appliedUpdates: list[AppliedAiUpdate]
    board: BoardResponse
