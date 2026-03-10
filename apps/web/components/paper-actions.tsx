"use client";

import { useEffect, useMemo, useState } from "react";

type Props = {
  paperId: string;
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
        {saved ? "Unsave" : "Save"}
      </button>
      <button
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
        {dismissed ? "Dismissed" : "Dismiss"}
      </button>
      <button
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
        Open
      </button>
    </div>
  );
}
