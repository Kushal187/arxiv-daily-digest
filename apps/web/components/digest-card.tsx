"use client";

import Link from "next/link";
import { useState } from "react";
import type { DigestPaper } from "@arxiv-digest/shared";
import { PaperActions } from "./paper-actions";

export function DigestCard({ paper }: { paper: DigestPaper }) {
  const [hidden, setHidden] = useState(false);

  if (hidden || paper.isDismissed) {
    return null;
  }

  return (
    <article className="paper-card">
      <div className="card-topline">
        <span className="score-badge">Score {paper.score.toFixed(2)}</span>
        <span className="cluster-chip">{paper.clusterLabel}</span>
      </div>
      <h2>
        <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
      </h2>
      <p className="subtle">
        {paper.authors.join(", ")} · {new Date(paper.publishedAt).toLocaleDateString()}
      </p>
      <p>{paper.abstract}</p>
      <div className="chip-row">
        {paper.categories.map((category) => (
          <span key={category} className="meta-chip">
            {category}
          </span>
        ))}
        {paper.topics
          .filter((topic) => !topic.isHidden)
          .map((topic) => (
            <span key={topic.slug} className="topic-chip">
              {topic.slug}
            </span>
          ))}
      </div>
      <div className="chip-row">
        {paper.reasons.map((reason) => (
          <span key={`${paper.id}-${reason.type}-${reason.label}`} className="reason-chip">
            {reason.label}
          </span>
        ))}
      </div>
      <PaperActions
        paperId={paper.id}
        initialSaved={paper.isSaved}
        initialDismissed={paper.isDismissed}
        onDismissed={() => setHidden(true)}
      />
    </article>
  );
}
