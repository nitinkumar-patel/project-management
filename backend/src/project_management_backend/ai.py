import os

from openai import OpenAI

AI_MODEL = "gpt-4o-mini"
CONNECTIVITY_PROMPT = "What is 2+2? Reply with only the number."


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
