import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "../../lib/auth";
import { getFollowedAuthorsDashboard } from "../../lib/queries";

export default async function AuthorsPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const dashboard = await getFollowedAuthorsDashboard(session.user.id);

  return (
    <main className="page">
      <section className="page-header">
        <p className="eyebrow">authors</p>
        <h1>Followed authors</h1>
        <p className="page-description">
          Author matching now handles exact names, initials, and small last-name typos.
        </p>
      </section>

      <section className="authors-page">
        <div className="authors-summary">
          <p className="section-note">
            {dashboard.authors.length
              ? `Tracking ${dashboard.authors.length} author${dashboard.authors.length === 1 ? "" : "s"}.`
              : "No authors followed yet."}
          </p>
          <Link href="/settings" className="action-link prominent">
            edit followed authors
          </Link>
        </div>

        {dashboard.authors.length ? (
          <div className="authors-grid">
            {dashboard.authors.map((author) => (
              <section key={author.name} className="author-block">
                <div className="author-block-header">
                  <h2>{author.name}</h2>
                  <span className="author-count">
                    {author.recentMatchCount} recent match{author.recentMatchCount === 1 ? "" : "es"}
                  </span>
                </div>
                {author.recentMatches.length ? (
                  <ul className="author-paper-list">
                    {author.recentMatches.map((paper) => (
                      <li key={paper.id}>
                        <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
                        <p className="paper-meta">
                          matched {paper.matchedPaperAuthor} ·{" "}
                          {new Date(paper.publishedAt).toLocaleDateString()}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="section-note">No recent papers matched this author yet.</p>
                )}
              </section>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>Add authors in settings to see them tracked here.</p>
          </div>
        )}

        {dashboard.recentPapers.length ? (
          <section className="detail-section">
            <h2>Recent papers from followed authors</h2>
            <div className="feed-list">
              {dashboard.recentPapers.map((paper) => (
                <article key={`${paper.followedAuthor}-${paper.id}`} className="paper-row">
                  <h3 className="paper-title">
                    <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
                  </h3>
                  <p className="paper-meta">
                    followed {paper.followedAuthor} · matched {paper.matchedPaperAuthor} ·{" "}
                    {new Date(paper.publishedAt).toLocaleDateString()}
                  </p>
                </article>
              ))}
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}
