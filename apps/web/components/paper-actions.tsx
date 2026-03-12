"use client";

import { useMemo, useState } from "react";
import type { InteractionType } from "@arxiv-digest/shared";

type Props = {
  paperId: string;
  paperUrl?: string;
  initialSaved: boolean;
  initialDismissed: boolean;
  compact?: boolean;
  allowDismiss?: boolean;
  onDismissedChange?: (dismissed: boolean) => void;
  onSavedChange?: (saved: boolean) => void;
  onInteractionCommitted?: (action: InteractionType) => void;
};

async function sendInteraction(paperId: string, action: InteractionType) {
  const response = await fetch("/api/interactions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ paperId, action })
  });

  if (!response.ok) {
    throw new Error("Interaction failed");
  }
}

export function PaperActions({
  paperId,
  paperUrl,
  initialSaved,
  initialDismissed,
  compact = false,
  allowDismiss = true,
  onDismissedChange,
  onSavedChange,
  onInteractionCommitted
}: Props) {
  const [saved, setSaved] = useState(initialSaved);
  const [dismissed, setDismissed] = useState(initialDismissed);
  const [pending, setPending] = useState({ save: false, dismiss: false });
  const [error, setError] = useState<string | null>(null);

  const classes = useMemo(
    () => `paper-actions${compact ? " compact" : ""}`,
    [compact]
  );

  async function toggleSave() {
    const nextSaved = !saved;
    setPending((current) => ({ ...current, save: true }));
    setError(null);
    setSaved(nextSaved);
    onSavedChange?.(nextSaved);

    try {
      const action: InteractionType = nextSaved ? "save" : "unsave";
      await sendInteraction(paperId, action);
      onInteractionCommitted?.(action);
    } catch {
      setSaved(!nextSaved);
      onSavedChange?.(!nextSaved);
      setError("Could not update your reading queue.");
    } finally {
      setPending((current) => ({ ...current, save: false }));
    }
  }

  async function toggleDismiss() {
    const nextDismissed = !dismissed;
    setPending((current) => ({ ...current, dismiss: true }));
    setError(null);
    setDismissed(nextDismissed);
    onDismissedChange?.(nextDismissed);

    try {
      const action: InteractionType = nextDismissed ? "dismiss" : "undismiss";
      await sendInteraction(paperId, action);
      onInteractionCommitted?.(action);
    } catch {
      setDismissed(!nextDismissed);
      onDismissedChange?.(!nextDismissed);
      setError("Could not update this digest item.");
    } finally {
      setPending((current) => ({ ...current, dismiss: false }));
    }
  }

  function handleOpen() {
    setError(null);
    void sendInteraction(paperId, "open")
      .then(() => onInteractionCommitted?.("open"))
      .catch(() => {
      // Navigation should still proceed if tracking fails.
      });
  }

  const saveButtonClass = saved ? "action-link action-link-save is-active" : "action-link action-link-save";

  return (
    <div className={classes}>
      <button
        type="button"
        className={saveButtonClass}
        aria-pressed={saved}
        disabled={pending.save}
        onClick={toggleSave}
      >
        {pending.save ? "saving..." : saved ? "remove" : "save"}
      </button>
      {allowDismiss ? (
        <button type="button" className="action-link" disabled={pending.dismiss} onClick={toggleDismiss}>
          {pending.dismiss ? "working..." : dismissed ? "undo dismiss" : "dismiss"}
        </button>
      ) : null}
      {paperUrl ? (
        <a
          className="action-link"
          href={paperUrl}
          target="_blank"
          rel="noreferrer"
          onClick={handleOpen}
        >
          open arxiv
        </a>
      ) : (
        <button
          className="action-link"
          type="button"
          onClick={() => {
            handleOpen();
            window.location.href = `/papers/${paperId}`;
          }}
        >
          open
        </button>
      )}
      {saved && !compact ? <p className="action-status-line">Saved to reading queue.</p> : null}
      {error ? <p className="inline-error">{error}</p> : null}
    </div>
  );
}
