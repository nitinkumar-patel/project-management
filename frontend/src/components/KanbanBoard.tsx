"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { AiChatSidebar } from "@/components/AiChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { moveCard, type BoardData, type Column } from "@/lib/kanban";
import * as api from "@/lib/api";

type KanbanBoardProps = {
  onLogout?: () => void;
};

export const KanbanBoard = ({ onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAiCollapsed, setIsAiCollapsed] = useState(false);
  const [error, setError] = useState("");

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  useEffect(() => {
    let isMounted = true;

    api
      .fetchBoard()
      .then((nextBoard) => {
        if (isMounted) {
          setBoard(nextBoard);
          setError("");
        }
      })
      .catch(() => {
        if (isMounted) {
          setError("Unable to load the board. Please try again.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const applyBoardUpdate = async (operation: () => Promise<BoardData>) => {
    try {
      const nextBoard = await operation();
      setBoard(nextBoard);
      setError("");
    } catch {
      setError("Unable to save the board change. Please try again.");
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || !over || active.id === over.id) {
      return;
    }

    const target = getMoveTarget(board.columns, active.id as string, over.id as string);
    if (!target) {
      return;
    }

    const prevBoard = board;
    const optimisticColumns = moveCard(board.columns, active.id as string, over.id as string);
    setBoard({ ...board, columns: optimisticColumns });

    api.moveCard(active.id as string, target.columnId, target.position)
      .then((nextBoard) => {
        setBoard(nextBoard);
        setError("");
      })
      .catch(() => {
        setBoard(prevBoard);
        setError("Unable to save the board change. Please try again.");
      });
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    applyBoardUpdate(() => api.renameColumn(columnId, title));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    applyBoardUpdate(() => api.createCard(columnId, title, details));
  };

  const handleDeleteCard = (_columnId: string, cardId: string) => {
    applyBoardUpdate(() => api.deleteCard(cardId));
  };

  const handleSendAiMessage = async (
    question: string,
    history: api.ChatMessage[]
  ) => {
    const response = await api.sendAiChat(question, history);
    setBoard(response.board);
    setError("");
    return response;
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  className="mt-4 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--secondary-purple)] hover:text-[var(--secondary-purple)]"
                >
                  Log out
                </button>
              )}
            </div>
          </div>
          {board && (
            <div className="flex flex-wrap items-center gap-4">
              {board.columns.map((column) => (
                <div
                  key={column.id}
                  className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
                >
                  <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                  {column.title}
                </div>
              ))}
            </div>
          )}
        </header>

        {error && (
          <div
            role="alert"
            className="rounded-2xl border border-[var(--stroke)] bg-white px-5 py-4 text-sm font-semibold text-[var(--secondary-purple)] shadow-[var(--shadow)]"
          >
            {error}
          </div>
        )}

        {isLoading && (
          <div className="rounded-3xl border border-[var(--stroke)] bg-white/80 p-8 text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)] shadow-[var(--shadow)]">
            Loading board...
          </div>
        )}

        {board && (
          <div
            className={
              isAiCollapsed
                ? "grid gap-6 xl:grid-cols-[minmax(0,1fr)_72px]"
                : "grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]"
            }
          >
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <section className="grid gap-6 lg:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                  />
                ))}
              </section>
              <DragOverlay>
                {activeCard ? (
                  <div className="w-[260px]">
                    <KanbanCardPreview card={activeCard} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
            <AiChatSidebar
              onSend={handleSendAiMessage}
              isCollapsed={isAiCollapsed}
              onToggle={() => setIsAiCollapsed((current) => !current)}
            />
          </div>
        )}
      </main>
    </div>
  );
};

const getMoveTarget = (
  columns: Column[],
  activeId: string,
  overId: string
): { columnId: string; position: number } | null => {
  const targetColumn = columns.find(
    (column) => column.id === overId || column.cardIds.includes(overId)
  );
  if (!targetColumn) {
    return null;
  }

  if (targetColumn.id === overId) {
    return {
      columnId: targetColumn.id,
      position: targetColumn.cardIds.filter((cardId) => cardId !== activeId).length,
    };
  }

  // Use the card's index in the unfiltered list so same-column forward moves
  // resolve correctly (filtering out activeId shifts overId's index when
  // activeId precedes overId, causing an off-by-one on the server).
  const position = targetColumn.cardIds.indexOf(overId);

  return {
    columnId: targetColumn.id,
    position: position === -1 ? targetColumn.cardIds.length : position,
  };
};
