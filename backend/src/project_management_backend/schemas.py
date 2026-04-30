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
