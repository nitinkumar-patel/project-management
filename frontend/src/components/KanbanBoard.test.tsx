import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const mockBoardResponse = (board: BoardData = initialData) => {
  vi.mocked(fetch).mockResolvedValue({
    ok: true,
    json: async () => board,
  } as Response);
};

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders loading state then five columns", async () => {
    mockBoardResponse();
    render(<KanbanBoard />);

    expect(screen.getByText(/loading board/i)).toBeInTheDocument();
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("shows an error when the board load fails", async () => {
    vi.mocked(fetch).mockRejectedValue(new Error("No API"));
    render(<KanbanBoard />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to load the board. Please try again."
    );
  });

  it("renames a column", async () => {
    const renamedBoard = {
      ...initialData,
      columns: initialData.columns.map((column) =>
        column.id === "col-backlog" ? { ...column, title: "New Name" } : column
      ),
    };
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => initialData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => renamedBoard,
      } as Response);

    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();

    expect(input).toHaveValue("New Name");
    expect(fetch).toHaveBeenLastCalledWith(
      "/api/columns/col-backlog",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ title: "New Name" }),
      })
    );
  });

  it("adds and removes a card", async () => {
    const addedBoard = {
      ...initialData,
      cards: {
        ...initialData.cards,
        "card-new": { id: "card-new", title: "New card", details: "Notes" },
      },
      columns: initialData.columns.map((column) =>
        column.id === "col-backlog"
          ? { ...column, cardIds: [...column.cardIds, "card-new"] }
          : column
      ),
    };
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => initialData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => addedBoard,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => initialData,
      } as Response);

    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(await within(column).findByText("Align roadmap themes")).toBeInTheDocument();
    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("refreshes the board after an AI update", async () => {
    const aiBoard = {
      ...initialData,
      cards: {
        ...initialData.cards,
        "card-ai": {
          id: "card-ai",
          title: "AI generated card",
          details: "Created by the assistant.",
        },
      },
      columns: initialData.columns.map((column) =>
        column.id === "col-backlog"
          ? { ...column, cardIds: [...column.cardIds, "card-ai"] }
          : column
      ),
    };
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => initialData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: "I added a card.",
          appliedUpdates: [
            { type: "create_card", summary: "Created card 'AI generated card'." },
          ],
          board: aiBoard,
        }),
      } as Response);

    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);

    await userEvent.type(
      screen.getByLabelText(/message/i),
      "Create an AI generated card"
    );
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByText("AI generated card")).toBeInTheDocument();
    expect(screen.getByText("Created card 'AI generated card'.")).toBeInTheDocument();
  });

  it("collapses and expands the AI assistant without losing chat state", async () => {
    const aiBoard = initialData;
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => initialData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: "I can still see the board.",
          appliedUpdates: [],
          board: aiBoard,
        }),
      } as Response);

    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);

    await userEvent.type(screen.getByLabelText(/message/i), "Can you help?");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));
    expect(await screen.findByText("I can still see the board.")).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: /collapse ai assistant/i })
    );
    expect(screen.queryByText("I can still see the board.")).not.toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: /expand ai assistant/i })
    );
    expect(screen.getByText("I can still see the board.")).toBeInTheDocument();
  });
});
