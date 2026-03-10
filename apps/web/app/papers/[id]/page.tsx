import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { PaperActions } from "../../../components/paper-actions";
import { auth } from "../../../lib/auth";
import { env } from "../../../lib/env";
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
        <p>{paper.abstract}</p>
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
        <div className="detail-section">
          <h2>Explain this paper</h2>
          {env.explainEnabled ? (
            response.summary ? (
              <p>{response.summary}</p>
            ) : (
              <p className="page-description">No cached explanation exists yet for this paper.</p>
            )
          ) : (
            <p className="page-description">Explanation is disabled in this environment.</p>
          )}
        </div>
      </article>
    </main>
  );
}
