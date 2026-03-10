import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "../../lib/auth";
import { getSavedPapers } from "../../lib/queries";

export default async function SavedPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const saved = await getSavedPapers(session.user.id);

  return (
    <main className="page">
      <section className="page-header">
        <p className="eyebrow">saved</p>
        <h1>Your reading queue</h1>
      </section>
      <section className="feed-list">
        {saved.length ? (
          <>
            {saved.map((paper) => (
              <article key={paper.id} className="paper-row">
                <h2 className="paper-title">
                  <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
                </h2>
                <p className="paper-meta">
                  {paper.authors.join(", ")} · {new Date(paper.published_at).toLocaleDateString()}
                </p>
                <p className="paper-abstract expanded">{paper.abstract}</p>
                <div className="metadata-row">
                  {paper.categories.map((category) => (
                    <span key={category} className="metadata-tag">
                      {category.toLowerCase()}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </>
        ) : (
          <div className="empty-state">
            <p>You have not saved any papers yet.</p>
          </div>
        )}
      </section>
    </main>
  );
}
