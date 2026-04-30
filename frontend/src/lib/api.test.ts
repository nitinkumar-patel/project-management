import { initialData } from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  fetchBoard,
  moveCard,
  renameColumn,
  sendAiChat,
  updateCard,
} from "@/lib/api";

const mockFetch = (response: Partial<Response>) => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
};

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches the board", async () => {
    mockFetch({ ok: true, json: async () => initialData });

    await expect(fetchBoard()).resolves.toEqual(initialData);
    expect(fetch).toHaveBeenCalledWith("/api/board", {
      headers: { "Content-Type": "application/json" },
    });
  });

  it("sends board mutation requests", async () => {
    mockFetch({ ok: true, json: async () => initialData });

    await renameColumn("col-backlog", "Ideas");
    await createCard("col-backlog", "New card", "Details");
    await updateCard("card-1", "Updated", "Updated details");
    await moveCard("card-1", "col-review", 0);
    await deleteCard("card-1");

    expect(fetch).toHaveBeenNthCalledWith(
      1,
      "/api/columns/col-backlog",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ title: "Ideas" }),
      })
    );
    expect(fetch).toHaveBeenNthCalledWith(
      2,
      "/api/cards",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          columnId: "col-backlog",
          title: "New card",
          details: "Details",
        }),
      })
    );
    expect(fetch).toHaveBeenNthCalledWith(
      3,
      "/api/cards/card-1",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ title: "Updated", details: "Updated details" }),
      })
    );
    expect(fetch).toHaveBeenNthCalledWith(
      4,
      "/api/cards/card-1/move",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ columnId: "col-review", position: 0 }),
      })
    );
    expect(fetch).toHaveBeenNthCalledWith(
      5,
      "/api/cards/card-1",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("throws when the API request fails", async () => {
    mockFetch({ ok: false, status: 500 });

    await expect(fetchBoard()).rejects.toThrow(
      "API request failed with status 500."
    );
  });

  it("sends AI chat requests with conversation history", async () => {
    const aiResponse = {
      message: "The board looks healthy.",
      appliedUpdates: [],
      board: initialData,
    };
    mockFetch({ ok: true, json: async () => aiResponse });

    await expect(
      sendAiChat("What should I do next?", [
        { role: "assistant", content: "How can I help?" },
      ])
    ).resolves.toEqual(aiResponse);

    expect(fetch).toHaveBeenCalledWith(
      "/api/ai/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          question: "What should I do next?",
          history: [{ role: "assistant", content: "How can I help?" }],
        }),
      })
    );
  });
});
