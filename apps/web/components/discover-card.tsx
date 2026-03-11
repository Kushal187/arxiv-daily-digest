"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { getAreaLabel, getTopicLabel, type DigestPaper } from "@arxiv-digest/shared";
import { formatRelativeAge, formatTimestampDate } from "../lib/dates";
import { PaperActions } from "./paper-actions";

export function DiscoverCard({ paper }: { paper: DigestPaper }) {
  const [abstractOpen, setAbstractOpen] = useState(false);
  const [saved, setSaved] = useState(paper.isSaved);
  const visibleTopics = useMemo(() => paper.topics.filter((topic) => !topic.isHidden).slice(0, 2), [paper.topics]);
  const authors = paper.authors.slice(0, 2).join(", ");
  const overflowCount = Math.max(paper.authors.length - 2, 0);
  const primaryReason = paper.reasons[0]?.label ?? null;

  return (
    <article className="discover-card">
      <div className="discover-card-header">
        <span className="reason-pill">{formatRelativeAge(paper.publishedAt)}</span>
        {saved ? <span className="saved-pill">Saved</span> : null}
      </div>
      <h2 className="paper-title discover">
        <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
      </h2>
      <p className="paper-meta discover-meta">
        {authors}
        {overflowCount ? ` +${overflowCount}` : ""} · {formatTimestampDate(paper.publishedAt)}
      </p>
      {primaryReason ? <p className="reason-line discover-reason">{primaryReason}</p> : null}
      <div className="metadata-row discover-tag-row">
        {visibleTopics.map((topic) => (
          <span key={topic.slug} className="metadata-tag">
            {getTopicLabel(topic.slug)}
          </span>
        ))}
        {visibleTopics.length === 0 && paper.topics[0]?.areaSlug ? (
          <span className="metadata-tag">{getAreaLabel(paper.topics[0].areaSlug)}</span>
        ) : null}
      </div>
      <p className="paper-abstract discover-abstract">{paper.abstract}</p>
      <button
        type="button"
        className="inline-toggle"
        aria-expanded={abstractOpen}
        onClick={() => setAbstractOpen(true)}
      >
        read full abstract
      </button>
      <PaperActions
        paperId={paper.id}
        paperUrl={paper.url}
        initialSaved={paper.isSaved}
        initialDismissed={paper.isDismissed}
        compact
        allowDismiss={false}
        onSavedChange={setSaved}
      />

      {abstractOpen ? (
        <div className="discover-abstract-modal-backdrop" role="presentation" onClick={() => setAbstractOpen(false)}>
          <section
            className="discover-abstract-modal"
            role="dialog"
            aria-modal="true"
            aria-label={`Abstract for ${paper.title}`}
            onClick={(event) => event.stopPropagation()}
          >
            <header className="discover-abstract-modal-header">
              <h3>{paper.title}</h3>
              <button type="button" className="inline-toggle" onClick={() => setAbstractOpen(false)}>
                close
              </button>
            </header>
            <p className="paper-meta discover-meta">
              {authors}
              {overflowCount ? ` +${overflowCount}` : ""} · {formatTimestampDate(paper.publishedAt)}
            </p>
            <p className="discover-abstract-modal-content">{paper.abstract}</p>
          </section>
        </div>
      ) : null}
    </article>
  );
}
