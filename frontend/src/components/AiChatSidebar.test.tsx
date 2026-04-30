import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AiChatSidebar } from "@/components/AiChatSidebar";
import { initialData } from "@/lib/kanban";

describe("AiChatSidebar", () => {
  it("sends a message and renders the assistant response", async () => {
    const onSend = vi.fn().mockResolvedValue({
      message: "The board is balanced.",
      appliedUpdates: [],
      board: initialData,
    });

    render(<AiChatSidebar onSend={onSend} />);

    await userEvent.type(screen.getByLabelText(/message/i), "Summarize the board");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(onSend).toHaveBeenCalledWith(
      "Summarize the board",
      [
        {
          role: "assistant",
          content:
            "Ask me about the board, or ask me to create, edit, or move cards.",
        },
      ]
    );
    expect(await screen.findByText("The board is balanced.")).toBeInTheDocument();
  });

  it("shows applied updates from the AI response", async () => {
    const onSend = vi.fn().mockResolvedValue({
      message: "I added the card.",
      appliedUpdates: [{ type: "create_card", summary: "Created card 'Ship it'." }],
      board: initialData,
    });

    render(<AiChatSidebar onSend={onSend} />);

    await userEvent.type(screen.getByLabelText(/message/i), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByText("Applied updates")).toBeInTheDocument();
    expect(screen.getByText("Created card 'Ship it'.")).toBeInTheDocument();
  });

  it("shows an error when the AI request fails", async () => {
    const onSend = vi.fn().mockRejectedValue(new Error("No AI"));

    render(<AiChatSidebar onSend={onSend} />);

    await userEvent.type(screen.getByLabelText(/message/i), "Help");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to reach the AI assistant. Please try again."
    );
  });
});
