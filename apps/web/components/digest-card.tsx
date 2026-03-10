"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { TOPIC_TAXONOMY, type DigestPaper } from "@arxiv-digest/shared";
import { formatTimestampDate } from "../lib/dates";
import { PaperActions } from "./paper-actions";

const TOPIC_LABELS = new Map(TOPIC_TAXONOMY.map((topic) => [topic.slug, topic.label]));

export function DigestCard({ paper }: { paper: DigestPaper }) {
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(paper.isDismissed);
  const [saved, setSaved] = useState(paper.isSaved);
  const visibleTopics = useMemo(
    () => paper.topics.filter((topic) => !topic.isHidden).map((topic) => TOPIC_LABELS.get(topic.slug) ?? topic.slug),
    [paper.topics]
  );
  const primaryReason = paper.reasons[0];
  const secondaryReasons = paper.reasons.slice(1);

  if (dismissed) {
    return (
      <article className="paper-row dismissed-row">
        <p className="section-note">Dismissed from this digest.</p>
        <PaperActions
          paperId={paper.id}
          paperUrl={paper.url}
          initialSaved={saved}
          initialDismissed
          onSavedChange={setSaved}
          onDismissedChange={setDismissed}
        />
      </article>
    );
  }

  return (
    <article className="paper-row">
      <div className="paper-row-header">
        {saved ? <span className="saved-pill">Saved</span> : null}
        {primaryReason ? <span className="reason-pill">{primaryReason.label}</span> : null}
        {paper.clusterLabel !== "misc" ? <span className="meta-inline">{paper.clusterLabel}</span> : null}
      </div>
      <h2 className="paper-title">
        <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
      </h2>
      <p className="paper-meta">
        {paper.authors.join(", ")} · {formatTimestampDate(paper.publishedAt)}
      </p>
      <p className={expanded ? "paper-abstract expanded" : "paper-abstract"}>{paper.abstract}</p>
      <button
        type="button"
        className="inline-toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
      >
        {expanded ? "collapse abstract" : "expand abstract"}
      </button>
      <div className="metadata-row">
        {paper.categories.map((category) => (
          <span key={category} className="metadata-tag">
            {category.toLowerCase()}
          </span>
        ))}
        {visibleTopics.map((topic) => (
          <span key={topic} className="metadata-tag">
            {topic}
          </span>
        ))}
      </div>
      {secondaryReasons.length ? (
        <p className="reason-line">{secondaryReasons.map((reason) => reason.label).join(" · ")}</p>
      ) : null}
      <PaperActions
        paperId={paper.id}
        paperUrl={paper.url}
        initialSaved={paper.isSaved}
        initialDismissed={paper.isDismissed}
        onDismissedChange={setDismissed}
        onSavedChange={setSaved}
      />
    </article>
  );
}
