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
    <main className="grid">
      <article className="paper-detail">
        <p className="subtle">{paper.primaryCategory}</p>
        <h1>{paper.title}</h1>
        <p className="subtle">{paper.authors.join(", ")}</p>
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
            <span key={`${paper.id}-${reason.label}`} className="reason-chip">
              {reason.label}
            </span>
          ))}
        </div>
        <PaperActions
          paperId={paper.id}
          initialSaved={paper.isSaved}
          initialDismissed={paper.isDismissed}
        />
        <div className="section-block">
          <h2>Original paper</h2>
          <p>
            <Link href={paper.url} target="_blank">
              Open on arXiv
            </Link>
          </p>
        </div>
        <div className="section-block">
          <h2>Explain this paper</h2>
          {env.explainEnabled ? (
            response.summary ? (
              <p>{response.summary}</p>
            ) : (
              <p className="subtle">No cached explanation exists yet for this paper.</p>
            )
          ) : (
            <p className="subtle">Explanation is disabled in this environment.</p>
          )}
        </div>
      </article>
    </main>
  );
}
