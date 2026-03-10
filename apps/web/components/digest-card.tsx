"use client";

import Link from "next/link";
import { useState } from "react";
import type { DigestPaper } from "@arxiv-digest/shared";
import { PaperActions } from "./paper-actions";

export function DigestCard({ paper }: { paper: DigestPaper }) {
  const [hidden, setHidden] = useState(false);
  const [expanded, setExpanded] = useState(false);

  if (hidden || paper.isDismissed) {
    return null;
  }

  return (
    <article className="paper-row">
      <div className="paper-row-header">
        <span className="score-badge">{paper.score.toFixed(2)}</span>
        <span className="meta-inline">{paper.clusterLabel}</span>
      </div>
      <h2 className="paper-title">
        <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
      </h2>
      <p className="paper-meta">
        {paper.authors.join(", ")} · {new Date(paper.publishedAt).toLocaleDateString()}
      </p>
      <p className={expanded ? "paper-abstract expanded" : "paper-abstract"}>{paper.abstract}</p>
      <button className="inline-toggle" onClick={() => setExpanded((current) => !current)}>
        {expanded ? "collapse abstract" : "expand abstract"}
      </button>
      <div className="metadata-row">
        {paper.categories.map((category) => (
          <span key={category} className="metadata-tag">
            {category.toLowerCase()}
          </span>
        ))}
        {paper.topics
          .filter((topic) => !topic.isHidden)
          .map((topic) => (
            <span key={topic.slug} className="metadata-tag">
              {topic.slug}
            </span>
          ))}
      </div>
      {paper.reasons.length ? (
        <p className="reason-line">
          {paper.reasons.map((reason) => reason.label).join(" · ")}
        </p>
      ) : null}
      <PaperActions
        paperId={paper.id}
        paperUrl={paper.url}
        initialSaved={paper.isSaved}
        initialDismissed={paper.isDismissed}
        onDismissed={() => setHidden(true)}
      />
    </article>
  );
}
