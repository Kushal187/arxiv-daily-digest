"use client";

import { useMemo, useState } from "react";
import type { DigestResponse } from "@arxiv-digest/shared";
import { DigestCard } from "./digest-card";

type FeedFilter = "all" | "author" | "saved" | "fresh";

const FILTER_OPTIONS: { value: FeedFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "author", label: "Followed authors" },
  { value: "saved", label: "Saved-like" },
  { value: "fresh", label: "Fresh" }
];

function matchesFilter(filter: FeedFilter, paper: DigestResponse["papers"][number]) {
  if (filter === "all") {
    return true;
  }

  if (filter === "author") {
    return paper.reasons.some((reason) => reason.type === "author");
  }

  if (filter === "saved") {
    return paper.reasons.some((reason) => reason.type === "saved_similarity");
  }

  return paper.reasons.some((reason) => reason.type === "freshness");
}

export function DigestFeed({ digest }: { digest: DigestResponse }) {
  const [filter, setFilter] = useState<FeedFilter>("all");

  const counts = useMemo(() => {
    const next = new Map<FeedFilter, number>();
    for (const option of FILTER_OPTIONS) {
      next.set(option.value, digest.papers.filter((paper) => matchesFilter(option.value, paper)).length);
    }
    return next;
  }, [digest.papers]);

  const filtered = useMemo(
    () => digest.papers.filter((paper) => matchesFilter(filter, paper)),
    [digest.papers, filter]
  );

  return (
    <>
      <section className="feed-toolbar">
        <div className="filter-pills" role="tablist" aria-label="Feed filters">
          {FILTER_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={option.value === filter ? "filter-pill active" : "filter-pill"}
              onClick={() => setFilter(option.value)}
            >
              {option.label} ({counts.get(option.value) ?? 0})
            </button>
          ))}
        </div>
        {digest.didBackfillCategories ? (
          <p className="section-note">
            Expanded beyond your selected categories to keep this digest filled out.
          </p>
        ) : null}
      </section>

      <section className="feed-list">
        {filtered.length ? (
          filtered.map((paper) => <DigestCard key={paper.id} paper={paper} />)
        ) : (
          <div className="empty-state">
            <p>No papers match this filter for the selected digest.</p>
          </div>
        )}
      </section>
    </>
  );
}
