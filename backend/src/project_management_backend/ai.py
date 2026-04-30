import os
import json

from openai import OpenAI
from project_management_backend.schemas import AiStructuredOutput

AI_MODEL = "gpt-4o-mini"
CONNECTIVITY_PROMPT = "What is 2+2? Reply with only the number."
BOARD_AI_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "message": {"type": "string"},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["create_card", "edit_card", "move_card"],
                    },
                    "cardId": {"type": ["string", "null"]},
                    "columnId": {"type": ["string", "null"]},
                    "title": {"type": ["string", "null"]},
                    "details": {"type": ["string", "null"]},
                    "position": {"type": ["integer", "null"], "minimum": 0},
                },
                "required": [
                    "type",
                    "cardId",
                    "columnId",
                    "title",
                    "details",
                    "position",
                ],
            },
        },
    },
    "required": ["message", "operations"],
}


class MissingApiKeyError(Exception):
    pass


def get_openai_client() -> OpenAI:
    if not os.environ.get("OPENAI_API_KEY"):
        raise MissingApiKeyError("OPENAI_API_KEY is not configured.")

    return OpenAI()


def check_connectivity(client: OpenAI | None = None) -> str:
    openai_client = client or get_openai_client()
    response = openai_client.responses.create(
        model=AI_MODEL,
        input=CONNECTIVITY_PROMPT,
    )
    return response.output_text.strip()


def chat_about_board(
    board: dict,
    question: str,
    history: list[dict[str, str]],
    client: OpenAI | None = None,
) -> AiStructuredOutput:
    openai_client = client or get_openai_client()
    response = openai_client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a project management assistant. Answer the user and "
                    "optionally propose Kanban card updates. Only use these operations: "
                    "create_card, edit_card, move_card. Do not create, delete, or rename columns. "
                    "When no board change is needed, return an empty operations array."
                ),
            },
            *history,
            {
                "role": "user",
                "content": (
                    "Current board JSON:\n"
                    f"{json.dumps(board, indent=2)}\n\n"
                    f"User question:\n{question}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "kanban_ai_response",
                "strict": True,
                "schema": BOARD_AI_RESPONSE_SCHEMA,
            },
        },
    )
    content = response.choices[0].message.content or "{}"
    return parse_structured_output(content)


def parse_structured_output(content: str) -> AiStructuredOutput:
    return AiStructuredOutput.model_validate_json(content)
