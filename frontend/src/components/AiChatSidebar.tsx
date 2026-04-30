"use client";

import { useState, type FormEvent } from "react";
import type { AiChatResponse, ChatMessage } from "@/lib/api";

type AiChatSidebarProps = {
  onSend: (question: string, history: ChatMessage[]) => Promise<AiChatResponse>;
};

type DisplayMessage = ChatMessage & {
  updates?: string[];
};

export const AiChatSidebar = ({ onSend }: AiChatSidebarProps) => {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      role: "assistant",
      content:
        "Ask me about the board, or ask me to create, edit, or move cards.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || isSending) {
      return;
    }

    const history = messages.map(({ role, content }) => ({ role, content }));
    const userMessage: DisplayMessage = { role: "user", content: question };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setError("");
    setIsSending(true);

    try {
      const response = await onSend(question, history);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.message,
          updates: response.appliedUpdates.map((update) => update.summary),
        },
      ]);
    } catch {
      setError("Unable to reach the AI assistant. Please try again.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className="flex max-h-[760px] min-h-[520px] flex-col rounded-[32px] border border-[var(--stroke)] bg-[var(--navy-dark)] p-5 text-white shadow-[var(--shadow)]">
      <div className="border-b border-white/10 pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-white/55">
          AI Assistant
        </p>
        <h2 className="mt-2 font-display text-2xl font-semibold">Board Copilot</h2>
        <p className="mt-2 text-sm leading-6 text-white/65">
          Ask for a summary, or request card changes. Approved AI updates refresh
          the board automatically.
        </p>
      </div>

      <div
        className="mt-5 flex flex-1 flex-col gap-3 overflow-y-auto pr-1"
        aria-live="polite"
      >
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={
              message.role === "user"
                ? "ml-8 rounded-2xl bg-[var(--primary-blue)] px-4 py-3 text-sm leading-6"
                : "mr-4 rounded-2xl bg-white/10 px-4 py-3 text-sm leading-6 text-white/85"
            }
          >
            <p>{message.content}</p>
            {message.updates && message.updates.length > 0 && (
              <div className="mt-3 rounded-xl border border-[var(--accent-yellow)]/40 bg-[var(--accent-yellow)]/10 px-3 py-2">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent-yellow)]">
                  Applied updates
                </p>
                <ul className="mt-2 space-y-1 text-xs text-white/80">
                  {message.updates.map((update) => (
                    <li key={update}>{update}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-4 text-sm font-semibold text-[var(--accent-yellow)]">
          {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label
          htmlFor="ai-chat-message"
          className="text-xs font-semibold uppercase tracking-[0.2em] text-white/55"
        >
          Message
        </label>
        <textarea
          id="ai-chat-message"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the AI to summarize, create, edit, or move cards..."
          rows={4}
          className="w-full resize-none rounded-2xl border border-white/10 bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--accent-yellow)]"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-55"
        >
          {isSending ? "Thinking..." : "Send to AI"}
        </button>
      </form>
    </aside>
  );
};
