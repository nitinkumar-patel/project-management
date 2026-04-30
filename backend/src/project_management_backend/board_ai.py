from project_management_backend import ai, database
from project_management_backend.schemas import (
    AiBoardOperation,
    AiChatMessage,
    AiStructuredOutput,
    AppliedAiUpdate,
)


class InvalidAiOperationError(Exception):
    pass


def handle_chat(question: str, history: list[AiChatMessage]) -> dict:
    board = database.get_board()
    structured_output = ai.chat_about_board(
        board=board,
        question=question,
        history=[message.model_dump() for message in history],
    )
    try:
        applied_updates = apply_operations(structured_output.operations, board)
    except database.NotFoundError as e:
        raise InvalidAiOperationError(str(e)) from e
    return {
        "message": structured_output.message,
        "appliedUpdates": [update.model_dump() for update in applied_updates],
        "board": database.get_board(),
    }


def apply_operations(
    operations: list[AiBoardOperation],
    board: dict,
) -> list[AppliedAiUpdate]:
    validate_operations(operations, board)

    applied_updates: list[AppliedAiUpdate] = []
    # Track card IDs including ones created mid-batch so chained operations can
    # reference newly created cards by their server-assigned ID.
    card_ids = set(board["cards"].keys())

    with database.connect() as conn:
        for operation in operations:
            if operation.type == "create_card":
                new_id = database._create_card(
                    conn,
                    operation.columnId or "",
                    operation.title or "",
                    operation.details or "",
                )
                card_ids.add(new_id)
                applied_updates.append(
                    AppliedAiUpdate(
                        type=operation.type,
                        summary=f"Created card '{operation.title}'.",
                    )
                )
            elif operation.type == "edit_card":
                if (operation.cardId or "") not in card_ids:
                    raise InvalidAiOperationError("AI requested an invalid card.")
                database._update_card(
                    conn,
                    operation.cardId or "",
                    operation.title or "",
                    operation.details or "",
                )
                applied_updates.append(
                    AppliedAiUpdate(
                        type=operation.type,
                        summary=f"Edited card '{operation.cardId}'.",
                    )
                )
            elif operation.type == "move_card":
                if (operation.cardId or "") not in card_ids:
                    raise InvalidAiOperationError("AI requested an invalid card.")
                database._move_card(
                    conn,
                    operation.cardId or "",
                    operation.columnId or "",
                    operation.position or 0,
                )
                applied_updates.append(
                    AppliedAiUpdate(
                        type=operation.type,
                        summary=f"Moved card '{operation.cardId}'.",
                    )
                )

    return applied_updates


def validate_operations(operations: list[AiBoardOperation], board: dict) -> None:
    column_ids = {column["id"] for column in board["columns"]}
    card_ids = set(board["cards"].keys())

    for operation in operations:
        if operation.type == "create_card":
            if not operation.columnId or operation.columnId not in column_ids:
                raise InvalidAiOperationError("AI requested an invalid column.")
            if not operation.title:
                raise InvalidAiOperationError("AI requested a card without a title.")
        elif operation.type == "edit_card":
            if not operation.cardId or operation.cardId not in card_ids:
                raise InvalidAiOperationError("AI requested an invalid card.")
            if not operation.title:
                raise InvalidAiOperationError("AI requested a card edit without a title.")
            if operation.details is None:
                raise InvalidAiOperationError("AI requested a card edit without details.")
        elif operation.type == "move_card":
            if not operation.cardId or operation.cardId not in card_ids:
                raise InvalidAiOperationError("AI requested an invalid card.")
            if not operation.columnId or operation.columnId not in column_ids:
                raise InvalidAiOperationError("AI requested an invalid column.")
            if operation.position is None:
                raise InvalidAiOperationError("AI requested a move without a position.")
