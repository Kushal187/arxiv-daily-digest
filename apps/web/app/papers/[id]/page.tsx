import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { getTopicLabel } from "@arxiv-digest/shared";
import { ExpandableAbstract } from "../../../components/expandable-abstract";
import { PaperActions } from "../../../components/paper-actions";
import { PaperSummary } from "../../../components/paper-summary";
import { auth } from "../../../lib/auth";
import { fetchPaper } from "../../../lib/worker";

export default async function PaperDetailPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const { id } = await params;
  const response = await fetchPaper(session.user.id, id);

  if (!response.paper) {
    notFound();
  }

  const paper = response.paper;

  return (
    <main className="page">
      <article className="paper-detail">
        <p className="eyebrow">{paper.primaryCategory.toLowerCase()}</p>
        <h1 className="paper-title detail">{paper.title}</h1>
        <p className="paper-meta">{paper.authors.join(", ")}</p>
        <PaperSummary summary={response.summary} summarySource={response.summarySource} />
        <ExpandableAbstract abstract={paper.abstract} />
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
                {getTopicLabel(topic.slug)}
              </span>
            ))}
        </div>
        {paper.reasons.length ? <p className="reason-line">{paper.reasons.map((reason) => reason.label).join(" · ")}</p> : null}
        <PaperActions
          paperId={paper.id}
          paperUrl={paper.url}
          initialSaved={paper.isSaved}
          initialDismissed={paper.isDismissed}
        />
        <div className="detail-section">
          <h2>Original paper</h2>
          <p>
            <Link href={paper.url} target="_blank">
              Open on arXiv
            </Link>
          </p>
        </div>
      </article>
    </main>
  );
}
