import type { BoardData } from "@/lib/kanban";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AppliedAiUpdate = {
  type: string;
  summary: string;
};

export type AiChatResponse = {
  message: string;
  appliedUpdates: AppliedAiUpdate[];
  board: BoardData;
};

const requestJson = async <T>(
  path: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}.`);
  }

  return response.json();
};

const requestBoard = (path: string, options: RequestInit = {}) =>
  requestJson<BoardData>(path, options);

export const fetchBoard = () => requestBoard("/api/board");

export const renameColumn = (columnId: string, title: string) =>
  requestBoard(`/api/columns/${columnId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });

export const createCard = (columnId: string, title: string, details: string) =>
  requestBoard("/api/cards", {
    method: "POST",
    body: JSON.stringify({ columnId, title, details }),
  });

export const updateCard = (cardId: string, title: string, details: string) =>
  requestBoard(`/api/cards/${cardId}`, {
    method: "PATCH",
    body: JSON.stringify({ title, details }),
  });

export const moveCard = (cardId: string, columnId: string, position: number) =>
  requestBoard(`/api/cards/${cardId}/move`, {
    method: "POST",
    body: JSON.stringify({ columnId, position }),
  });

export const deleteCard = (cardId: string) =>
  requestBoard(`/api/cards/${cardId}`, {
    method: "DELETE",
  });

export const sendAiChat = (question: string, history: ChatMessage[]) =>
  requestJson<AiChatResponse>("/api/ai/chat", {
    method: "POST",
    body: JSON.stringify({ question, history }),
  });
