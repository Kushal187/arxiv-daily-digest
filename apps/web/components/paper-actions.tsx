"use client";

import { useEffect, useMemo, useState } from "react";

type Props = {
  paperId: string;
  paperUrl?: string;
  initialSaved: boolean;
  initialDismissed: boolean;
  compact?: boolean;
  onDismissed?: () => void;
};

async function sendInteraction(paperId: string, action: string) {
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
  onDismissed
}: Props) {
  const [saved, setSaved] = useState(initialSaved);
  const [dismissed, setDismissed] = useState(initialDismissed);
  const [isPending, setIsPending] = useState(false);

  const classes = useMemo(
    () => `paper-actions${compact ? " compact" : ""}`,
    [compact]
  );

  useEffect(() => {
    if (dismissed && onDismissed) {
      onDismissed();
    }
  }, [dismissed, onDismissed]);

  return (
    <div className={classes}>
      <button
        className="action-link"
        disabled={isPending}
        onClick={async () => {
          try {
            setIsPending(true);
            const action = saved ? "unsave" : "save";
            await sendInteraction(paperId, action);
            setSaved(!saved);
          } finally {
            setIsPending(false);
          }
        }}
      >
        {saved ? "saved" : "save"}
      </button>
      <button
        className="action-link"
        disabled={isPending || dismissed}
        onClick={async () => {
          try {
            setIsPending(true);
            await sendInteraction(paperId, "dismiss");
            setDismissed(true);
          } finally {
            setIsPending(false);
          }
        }}
      >
        {dismissed ? "dismissed" : "dismiss"}
      </button>
      {paperUrl ? (
        <a
          className="action-link"
          href={paperUrl}
          target="_blank"
          rel="noreferrer"
          onClick={async (event) => {
            event.preventDefault();
            if (isPending) {
              return;
            }

            try {
              setIsPending(true);
              await sendInteraction(paperId, "open");
              window.open(paperUrl, "_blank", "noopener,noreferrer");
            } finally {
              setIsPending(false);
            }
          }}
        >
          open arxiv
        </a>
      ) : (
        <button
          className="action-link"
          disabled={isPending}
          onClick={async () => {
            try {
              setIsPending(true);
              await sendInteraction(paperId, "open");
              window.location.href = `/papers/${paperId}`;
            } finally {
              setIsPending(false);
            }
          }}
        >
          open
        </button>
      )}
    </div>
  );
}
