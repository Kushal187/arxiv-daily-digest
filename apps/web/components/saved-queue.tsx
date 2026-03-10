"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { TOPIC_TAXONOMY } from "@arxiv-digest/shared";
import { formatTimestampDate } from "../lib/dates";
import { PaperActions } from "./paper-actions";

type SavedPaper = {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
  categories: string[];
  published_at: string;
  saved_at: string;
  url: string;
  visible_topics: { slug: string; confidence: number }[];
};

const TOPIC_LABELS = new Map<string, string>(TOPIC_TAXONOMY.map((topic) => [topic.slug, topic.label]));

export function SavedQueue({ papers }: { papers: SavedPaper[] }) {
  const [sort, setSort] = useState<"saved" | "published">("saved");
  const [hiddenIds, setHiddenIds] = useState<string[]>([]);

  const sorted = useMemo(() => {
    const visible = papers.filter((paper) => !hiddenIds.includes(paper.id));
    return [...visible].sort((left, right) =>
      sort === "saved"
        ? right.saved_at.localeCompare(left.saved_at)
        : right.published_at.localeCompare(left.published_at)
    );
  }, [hiddenIds, papers, sort]);

  return (
    <>
      <section className="feed-toolbar">
        <div className="filter-pills" role="tablist" aria-label="Queue sorting">
          <button
            type="button"
            className={sort === "saved" ? "filter-pill active" : "filter-pill"}
            onClick={() => setSort("saved")}
          >
            Recently saved
          </button>
          <button
            type="button"
            className={sort === "published" ? "filter-pill active" : "filter-pill"}
            onClick={() => setSort("published")}
          >
            Recently published
          </button>
        </div>
      </section>

      <section className="feed-list">
        {sorted.map((paper) => (
          <article key={paper.id} className="paper-row">
            <h2 className="paper-title">
              <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
            </h2>
            <p className="paper-meta">
              {paper.authors.join(", ")} · saved {formatTimestampDate(paper.saved_at)} · published{" "}
              {formatTimestampDate(paper.published_at)}
            </p>
            <p className="paper-abstract expanded">{paper.abstract}</p>
            <div className="metadata-row">
              {paper.categories.map((category) => (
                <span key={category} className="metadata-tag">
                  {category.toLowerCase()}
                </span>
              ))}
              {paper.visible_topics.map((topic) => (
                <span key={topic.slug} className="metadata-tag">
                  {TOPIC_LABELS.get(topic.slug) ?? topic.slug}
                </span>
              ))}
            </div>
            <PaperActions
              paperId={paper.id}
              paperUrl={paper.url}
              initialSaved
              initialDismissed={false}
              allowDismiss={false}
              compact
              onSavedChange={(saved) => {
                if (!saved) {
                  setHiddenIds((current) => [...current, paper.id]);
                }
              }}
            />
          </article>
        ))}
      </section>
    </>
  );
}
